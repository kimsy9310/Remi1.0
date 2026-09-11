# -*- coding: utf-8 -*-
"""
v2 온톨로지(L·A·M·C·S·R) → MixtureModel 어댑터.

왜 새로 쓰는가
--------------
엔진의 ontology.py 는 v1 3층(structure_class · attributes(SA.*) · ingredients)을
읽는다. v2 는 6층이고 키 이름이 전부 다르다. 그래서 v1 로더에 v2 를 넣으면
**예외 없이 빈 객체**가 나온다. 실측값이다.

    v1 엔진 + v1 온톨로지 : structure_classes 3 · params 29 · sensory 55
    v1 엔진 + v2 온톨로지 : structure_classes 0 · params  0 · sensory  0

조용히 비는 쪽이 터지는 쪽보다 위험하다. 그래서 v1 로더를 고쳐 쓰지 않고,
스펙이 정본으로 지정한 tests/loader_reference.py 를 그대로 불러다 쓴다.
그 파일에 담긴 네 규칙(alias 접기 · 스코프 정규화 · R-1 합성 · 활성 term 만
도달성 검사)은 각각 스모크테스트 실패에서 나온 것이라 다시 구현하면 안 된다.

이 모듈이 하는 일은 그 조립 결과를 mixture.py 의 계약에 맞추는 것뿐이다.

  1. 필러 행 제거      — assemble() 은 팔레트 전체에 대해 Γ₀ 를 만들지만
                          mixture.py 는 필러를 뺀 자유변수로 파라미터화한다.
                          스펙 불변식 8 에 따라 계수는 이미 필러 기준이므로
                          필러 행은 빠지는 것이 맞다.
  2. 스케일 산출       — Γ₀ 는 "1 표준편차당" 이다. 재료의 작업 범위에서
                          zsd 를 만들어 넘긴다. 이게 없으면 모형이 1 pp 를
                          1 SD 로 읽어 ±3 척도에서 +20 을 뱉는다.
  3. Λ 를 (q, m) 으로   — 엣지별 확신도를 재료별 최솟값으로 뭉개지 않는다.

사용
----
    from formulator.v2adapter import V2Ontology

    onto = V2Ontology()                       # 기본 경로 자동 탐색
    built = onto.build("icecream",
                       palette=[...],         # ING.* 목록 (필러 포함)
                       bounds={"ING.allulose": (0.0, 15.0), ...})
    built.model                               # 적합된 MixtureModel
    built.y_terms                             # 반응 축 이름
"""
from __future__ import annotations

import importlib.util
import os
import sys
from dataclasses import dataclass, field

import numpy as np
import yaml

from .mixture import MixtureModel, propose


# 이 파일 기준: engine/formulator/v2adapter.py → 프로젝트 루트는 두 단계 위
_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT = os.path.abspath(os.path.join(_HERE, "..", ".."))
DEFAULT_ROOT = os.path.join(_PROJECT, "ontology_v2")

# 작업 범위의 폭을 몇 SD 로 볼 것인가. zsd = (상한 - 하한) / RANGE_TO_SD.
#
# 2026-09-11: 4.0 -> 2.0 (docs/척도정의_전략.md 5절, 사용자 승인).
#   4.0 은 "범위를 ±2 SD 로 본다" 는 정규 근사였고 근거가 없었다. 2.0 은
#   "하한이 -1, 상한이 +1" - DoE 의 코드 단위이고, 온톨로지 사전이 실험계획의
#   코드 단위로 쓰인 지식이라 이쪽이 자연스러운 읽기다.
#   실측 18건에서 전 구간 이동량이 1~2 단위였는데 4.0 은 강한 효과에 4 단위를
#   배정해 사전이 2~4배 과대했다. JND 로 환산하면 2.0 에서 1 단계 ≈ 1.3 JND 로
#   "1 단계 ≈ 1 JND" 정의와 맞아떨어진다.
#   효과: 재료 1%p 당 관능 효과가 절반 -> 제안 이동 폭이 약 2배, 예측이 덜 부풀려짐.
RANGE_TO_SD = 2.0
FALLBACK_SD = 0.5          # 범위도 x0 도 없을 때의 최후 기본값
UNIVERSAL_AXES_FILE = "layerM_universal_axes.yaml"   # 전 프로파일 기본 카드
FILLER_HEADROOM = 2.0      # 기준 배합에서 필러에 남겨 두는 최소 몫(총량 대비 %)

# 제품은 더 이상 여기 없다. projects/<이름>/ 폴더에 산다(2026-09-10).
#
# 왜 옮겼나 — 스펙 2.3 이 활성 맥락을 SC x APP x ST 로만 정의한다. 제품
# 차원이 없다. 그런데 등록부에 제품이 제형처럼 올라 있었고, 그래서 제품의
# 정체성 축·실측 컬럼 매핑이 온톨로지 안에 들어앉아 있었다. 제형은 칸의
# 개수를 정하고 제품이 칸의 내용을 채우는 것이 원래 설계다.
#
# 정본 로더(tests/loader_reference.py)의 PROFILES 를 함부로 편집하지 않는다.
# 제품 제거처럼 등록부 자체가 틀린 경우만 거기서 고치고, 나머지는 여기서
# 병합한다.
PROJECTS_DIR = "projects"

EXTRA_PROFILES = {
    # 2026-09-11: 비었다. suspension_hotsauce 를 지웠다 - 제품은 온톨로지에 없다.
    # 사용자 근거 셋: 보안(한 사용자의 제품을 다른 사용자가 보면 안 된다) ·
    # 학습과 제품의 구분 · ID 무한 증식. 제형이 향 칸 둘을 갖는다는 사실은
    # STRUCTURE 의 flavor_slots 가 이미 들고 있어 잃는 것이 없다.
    # 제형 확장이 필요해지면 여기 쓴다. 제품은 projects/ 다.
}


def _load_reference_loader(root):
    """스펙이 정본으로 지정한 tests/loader_reference.py 를 모듈로 불러온다."""
    path = os.path.join(root, "tests", "loader_reference.py")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"정본 로더를 찾지 못했습니다: {path}\n"
            f"v2 온톨로지는 layers/ 와 tests/ 를 함께 둬야 합니다.")
    spec = importlib.util.spec_from_file_location("_remi_loader_ref", path)
    mod = importlib.util.module_from_spec(spec)
    # loader_reference 는 자기 위치 기준으로 ../layers 를 찾는다. 그대로 둔다.
    sys.modules["_remi_loader_ref"] = mod
    spec.loader.exec_module(mod)
    return mod


@dataclass
class BuiltModel:
    """조립 결과 한 묶음. 모형과, 그 모형을 어떻게 세웠는지의 근거."""
    model: MixtureModel
    palette: list
    filler: str
    y_terms: list
    Gamma0: np.ndarray            # (q_free, m) 필러 행 제거 후
    Lambda: np.ndarray            # (q_free, m) 엣지별
    Sigma0: np.ndarray            # (m, m)
    zsd: np.ndarray               # (q_free,)
    zbar: np.ndarray              # (q_free,)
    cards: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def report(self):
        """왜 이런 모형이 됐는지 사람이 읽는 요약."""
        L = [f"프로파일 반응축 {len(self.y_terms)}개 · 재료 {len(self.palette)}종"
             f"(필러 {self.filler} 제외 시 자유변수 {self.model.q})"]
        nz = int((self.Gamma0 != 0).sum())
        L.append(f"Γ₀ 비영 계수 {nz}/{self.Gamma0.size} "
                 f"({100 * nz / max(self.Gamma0.size, 1):.0f}%)")
        per_axis = (self.Gamma0 != 0).sum(axis=0)
        weak = [(t, int(c)) for t, c in zip(self.y_terms, per_axis) if c <= 2]
        if weak:
            L.append(f"조종 수단이 빈약한 축: {weak}")
        lv = sorted(set(np.round(self.Lambda[self.Gamma0 != 0], 2).tolist()))
        L.append(f"Λ 확신도 수준 {lv} (엣지별 유지)")
        for w in self.warnings:
            L.append(f"주의: {w}")
        return "\n".join("  " + s for s in L)


class V2Ontology:
    """v2 온톨로지를 읽고 mixture.py 용 입력으로 조립한다."""

    def __init__(self, root=None):
        self.root = root or DEFAULT_ROOT
        self._ref = _load_reference_loader(self.root)
        self.layers = os.path.join(self.root, "layers")
        self.stack = self._ref.load_stack(self.layers)
        # 정본 로더의 PROFILES + 제형 확장. 원본은 그대로 둔다.
        self.projects = self._load_projects()
        self.profiles = {**self._ref.PROFILES, **EXTRA_PROFILES,
                         **{k: v["profile"] for k, v in self.projects.items()}}
        self._ref.PROFILES = self.profiles      # validate/assemble 도 같은 표를 보게
        self._install_universal_axes()

    # ------------------------------------------------ 제품 (2026-09-10)
    def _load_projects(self):
        """
        projects/<이름>/product_card.yaml 을 읽어 세션 프로파일로 올린다.

        **온톨로지가 아니다.** 제품은 스펙 2.3 의 활성 맥락(SC x APP x ST)에
        자리가 없다. 그래서 layers/ 밖에 두고, 여는 세션에서만 프로파일처럼
        보이게 한다. 스코프는 `structure` 가 가리키는 제형에서 그대로
        물려받는다 - 제품이 제 스코프를 지어내지 못하게.

        두 층 (2026-09-11, 사용자 결정)
            AXIS_CARD     제형별 축 카드. layers/layerM_cards_<제형>.yaml. 공유된다
            PRODUCT_CARD  제품당 한 장. 제형 카드에서 벗어나는 것만 - drop 과 axes

        제품 카드는 통째 카드 목록이 아니라 **제형 카드 위에 얹는 차이**다.
        합성은 load_cards 래퍼가 한다 (_compose_product_cards).
        """
        root = os.path.join(os.path.dirname(self.root), PROJECTS_DIR)
        out = {}
        if not os.path.isdir(root):
            return out
        for name in sorted(os.listdir(root)):
            man = os.path.join(root, name, "product_card.yaml")
            if not os.path.exists(man):
                continue
            with open(man, encoding="utf-8") as fh:
                doc = yaml.safe_load(fh) or {}
            meta = doc.get("meta") or {}
            base = meta.get("structure")
            if base not in self._ref.PROFILES:
                raise ValueError(
                    f"프로젝트 {name} 의 structure '{base}' 가 STRUCTURE 에 없습니다. "
                    f"가능: {sorted(self._ref.PROFILES)}")
            pid = meta.get("id") or name
            if pid in self._ref.PROFILES or pid in EXTRA_PROFILES:
                # 2026-09-11 검증 결함 2. 제품 id 가 제형 이름과 겹치면 등록부에서
                # 제품이 제형을 조용히 덮어썼다 (beverage 카드 16 -> 6). 막는다.
                raise ValueError(
                    f"프로젝트 id '{pid}' 가 제형 이름과 겹칩니다. 제품 이름은 제형과 "
                    f"달라야 합니다. 제형: {sorted(self._ref.PROFILES)}")
            out[pid] = dict(
                dir=os.path.join(root, name),
                card=doc,
                structure=base,
                profile=dict(cards=[],               # 실물 파일 없음. 합성한다
                             scopes=set(self._ref.PROFILES[base]["scopes"])))
        return out

    def _compose_product_cards(self, pj, base_cards):
        """
        제형의 AXIS_CARD 위에 PRODUCT_CARD 의 차이를 얹는다.

            1 제형 카드를 전부 가져온다
            2 drop 에 있는 축을 뺀다
            3 axes: 제형에 있는 축이면 적힌 필드만 덮고(ko 는 안쪽까지),
                    없는 축이면 통째로 더한다
        보편 축 채우기는 이 다음에 래퍼가 평소처럼 한다.
        """
        doc = pj["card"]
        drop = set(doc.get("drop") or [])
        axes = doc.get("axes") or {}
        out = []
        seen = set()
        for c in base_cards:
            t = c["term_id"]
            if t in drop:
                continue
            c = dict(c)
            if t in axes:
                ov = dict(axes[t])
                ko_ov = ov.pop("ko", None)
                c.update(ov)
                if ko_ov:
                    c["ko"] = {**(c.get("ko") or {}), **ko_ov}
            c["from_product"] = t in axes
            out.append(c)
            seen.add(t)
        for t, full in axes.items():
            if t in seen or t in drop:
                continue
            c = dict(full)
            c["term_id"] = t
            c["from_product"] = True
            out.append(c)
        return out

    # ---------------------------------------------------------------- 조회
    @property
    def ingredients(self):
        return self.stack["ings"]

    @property
    def tags(self):
        return self.stack["tags"]

    # ------------------------------------------------ 보편 축 (2026-09-07)
    def _install_universal_axes(self):
        """
        기본맛을 전 프로파일의 기본 카드로 깐다.

        왜 여기인가. 기본맛은 제형이 함의하지 않는다 — 소금이 짜다는 것은
        에멀전이든 현탁액이든 언 것이든 같고, INGREDIENT 도 `scoped_to_structure_
        class: any` 로 그렇게 적고 있다. 그런데 M 카드는 제형 파일마다 손으로
        쓰였고, 그 결과 아이스크림에는 짠맛 카드가 없어 **물어볼 수조차** 없었다.

        INGREDIENT 의 2-tier 와 같은 방식으로 고친다. layerM_universal_axes.yaml 이
        모든 프로파일의 기본값이고, 제형 파일에 같은 term_id 카드가 있으면
        그쪽이 이긴다. 기본 tier 는 monitored 라 목적함수에는 안 들어간다 —
        core 로 올리는 것은 제형 카드가 하는 선언이다.

        정본 로더(tests/loader_reference.py)는 건드리지 않는다. 대신
        `_ref.load_cards` 를 감싼다. 앱 코드가 `onto._ref.load_cards(...)` 를
        직접 부르는 곳이 여럿이라, 여기서 감싸야 전부가 같은 것을 본다.
        """
        import yaml as _yaml
        path = os.path.join(self.layers, UNIVERSAL_AXES_FILE)
        if not os.path.exists(path):
            self.universal_axes = []
            return
        doc = _yaml.safe_load(open(path, encoding="utf-8")) or {}
        self.universal_axes = doc.get("measurement_cards") or []

        inner = self._ref.load_cards
        universal = self.universal_axes
        profiles = self.profiles

        def load_cards(profile, layers_dir=None):
            # 제품 카드는 layers/ 밖에 있다. 정본 로더가 layers_dir 과 파일명을
            # 이어 붙이는 구조라 절대 경로를 못 받는다. 여기서 가로챈다.
            pj = self.projects.get(profile)
            if pj:
                # 두 층: 제형의 AXIS_CARD 를 가져와 PRODUCT_CARD 의 차이를 얹는다
                base = pj["structure"]
                base_cards = inner(base, layers_dir) if layers_dir else inner(base)
                cards = self._compose_product_cards(pj, base_cards)
            else:
                cards = inner(profile, layers_dir) if layers_dir else inner(profile)
            have = {c["term_id"] for c in cards}
            scopes = sorted(s for s in profiles[profile]["scopes"] if s != "any")
            out = list(cards)
            for u in universal:
                if u["term_id"] in have:
                    continue                     # 제형 카드가 이긴다
                c = dict(u)
                c["active_in"] = scopes          # 문서용. 프로파일마다 다르다
                c["universal_default"] = True    # 어디서 왔는지 남긴다
                out.append(c)
            return out

        self._ref.load_cards = load_cards

    def label(self, term_id):
        """
        축의 한글 이름. LEXICON 의 ko 필드가 정본이다.

        이름을 M 카드에 두지 않는 이유: 같은 축이 프로파일 6곳에 카드로 나타나므로
        카드에 적으면 사본 6개가 따로 놀게 된다. 렉시콘 216개 항목 전부 ko 를
        가지고 있으니 고칠 곳은 언제나 한 군데다.
        """
        t = self.stack["lex"].get(term_id)
        ko = str((t or {}).get("ko", "")).strip()
        return ko or term_id.split(".")[-1]

    def ing_label(self, ing_id):
        """재료의 표시 이름. INGREDIENT 의 ko 가 정본이고 없으면 영문 label."""
        d = self.stack["ings"].get(ing_id) or {}
        ko = str(d.get("ko", "")).strip()
        if ko:
            return ko
        lab = str(d.get("label", "")).strip()
        return lab.split("(")[0].strip() or ing_id.replace("ING.", "")

    def card_ko(self, profile, term_id):
        """M 카드의 한글 블록(앵커·평가 주의·함정). 없으면 빈 dict."""
        for c in self._ref.load_cards(profile, self.layers):
            if c["term_id"] == term_id:
                return c.get("ko") or {}
        return {}

    def filler_of(self, profile):
        """S 프로파일이 선언한 필러. 없으면 모형을 세울 수 없다(스펙 §5.1)."""
        scopes = self.profiles[profile]["scopes"]
        for sp in self._s_candidates(profile):
            f = sp.get("filler")
            if not f:
                raise ValueError(
                    f"프로파일 {profile} 의 S 항목에 filler 선언이 없습니다(스펙 §5.1). "
                    f"필러 없이는 MixtureModel 을 세울 수 없습니다.")
            return f
        raise ValueError(
            f"프로파일 {profile} 에 대응하는 S 항목을 찾지 못했습니다. "
            f"스코프 {sorted(scopes)} 와 맞는 structure_profiles 항목이 없습니다.")

    def _s_candidates(self, profile):
        """
        프로파일 키에 맞는 S 항목들. 스펙 §5.10 대로 두 표기를 모두 맞춘다 —
        S 는 정체성 형태(SC.x|APP.y|ST.z), C 엣지는 점 경로(SC.x.y)를 쓴다.
        projects/ 의 제품 프로파일은 자기 S 항목이
        없고 상위(beverage)의 것을 쓴다(F7).
        """
        scopes = self.profiles[profile]["scopes"]
        exact, loose = [], []
        for sp in self.stack["S"]:
            parts = [sp.get("structure_class"), sp.get("application"), sp.get("state")]
            ident = "|".join(p for p in parts if p)
            if ident in scopes:
                exact.append(sp)              # 정체성이 그대로 맞는 것
            elif sp.get("structure_class") in scopes:
                loose.append(sp)              # 구조클래스만 맞는 것
        # 정체성이 맞는 것이 항상 우선한다.
        #
        # 이걸 구분하지 않으면 엉뚱한 S 항목이 붙는다 — 음료 프로파일의 스코프에
        # 'SC.emulsion.ow' 가 들어 있으므로, 같은 구조클래스인 아이스크림 항목이
        # 걸리고 부분 개수가 많다는 이유로 앞섰다. 그 결과 음료·소스가 전부
        # 아이스크림의 정의·경계를 물려받았다. 필러는 넷 다 ING.water 라서
        # 겉으로 드러나지 않았을 뿐이다.
        for grp in (exact, loose):
            grp.sort(key=lambda sp: -sum(1 for p in (sp.get("structure_class"),
                                                     sp.get("application"),
                                                     sp.get("state")) if p))
        return exact + loose

    def effects_for(self, profile):
        """이 프로파일에서 각 재료가 움직일 수 있는 축. 팔레트 고르기용."""
        scopes = self.profiles[profile]["scopes"]
        prox = {}
        for r in self.stack["R"]["relations_proxy"]:
            if r["scope"] in scopes:
                prox.setdefault(r["parameter"], []).append(r)
        return {g: self._ref.effects_of(self.stack["ings"][g], self.stack["tags"], prox, scopes)
                for g in self.stack["ings"]}

    def candidates(self, profile):
        """이 프로파일에서 하나라도 축을 움직이는 재료들."""
        return [g for g, e in self.effects_for(profile).items() if e]

    # ------------------------------------------------ 선례 없이 팔레트 세우기
    def core_terms(self, profile):
        """사용자에게 묻는 축. core 이면서 저장 격리(5.8)가 아닌 것."""
        return [c["term_id"] for c in self._ref.load_cards(profile, self.layers)
                if c["tier"] == "core" and c.get("evidence_required") != "sample_aged"]

    def slot_of(self, ing_id, profile=None):
        """
        재료가 속한 기능군의 (태그 id, 한글 이름).

        태그를 여럿 단 재료가 많아서 첫 번째를 집으면 엉뚱한 데로 간다 —
        토마토 페이스트는 [착색료, 향료, 고형분, 감칠맛, 증점제] 인데 첫 태그를
        쓰면 착색료(0~1%)가 되어 정작 쓰는 양을 담지 못한다. 그래서 **이
        제형에서 그 재료가 실제로 움직이는 축**을 가장 잘 설명하는 태그를 고른다.
        설명력이 같으면 사용 폭이 넓은 쪽을 쓴다 — 부재료가 아니라 주재료로
        다루는 슬롯이라는 뜻이다.
        """
        fts = [f for f in (self.stack["ings"][ing_id].get("function_tags") or [])
               if (self.stack["tags"].get(f) or {}).get("ko")]
        if not fts:
            return None, "기타"
        if profile is None or len(fts) == 1:
            ft = fts[0]
            return ft, self.stack["tags"][ft]["ko"]

        core = set(self.core_terms(profile))
        scopes = set(self.profiles[profile]["scopes"])

        def score(ft):
            t = self.stack["tags"][ft]
            hits = {e["to"] for e in (t.get("effects") or [])
                    if e.get("to") in core
                    and e.get("scoped_to_structure_class") in ("any", *scopes)}
            width = float((t.get("typical_use_pct") or [0, 0])[1])
            return (len(hits), width)

        ft = max(fts, key=score)
        return ft, self.stack["tags"][ft]["ko"]

    def slot_bounds(self, profile, ft):
        """
        기능군의 사용 범위 (하한, 상한, 출처).

        제형이 정하는 것은 제형에서 가져온다. 유지와 고형분은 제형에 따라
        자릿수가 다르므로(음료 0.01~15%, 소스 5~75%) 기능군 표준값으로
        뭉갤 수 없고, STRUCTURE 가 정의 파라미터로 이미 가지고 있다.
        """
        import re
        S_PARAM = {"FT.fat_source": ("P.fat_content", "P.oil_phase_fraction"),
                   "FT.particulate": ("P.solids_volume_fraction",)}
        for sp in self._s_candidates(profile):
            for want in S_PARAM.get(ft, ()):
                for p in (sp.get("parameters") or []):
                    if p.get("id") != want:
                        continue
                    m = re.search(r"(\d*\.?\d+)\s*(?:-|~|to)\s*(\d*\.?\d+)",
                                  str(p.get("plausible_range") or ""))
                    if not m:
                        continue
                    lo, hi = float(m.group(1)), float(m.group(2))
                    if hi <= 1.0:               # 분율로 적힌 파라미터는 % 로
                        lo, hi = lo * 100.0, hi * 100.0
                    return lo, hi, f"{sp.get('label', profile)} · {want}"
        t = self.stack["tags"].get(ft) or {}
        r = t.get("typical_use_pct")
        if r:
            return float(r[0]), float(r[1]), f"{t.get('ko', ft)} 기능군 통상 사용량"
        return 0.0, 5.0, "기본값"

    def default_palette(self, profile):
        """
        실측이 없어도 세울 수 있는 재료 후보.

        온톨로지는 어떤 재료가 이 제형에서 어떤 축을 움직이는지 이미 안다.
        없는 것은 "얼마나 쓰는가" 뿐이고 그것은 slot_bounds 가 채운다. 그래서
        선례가 없는 제형도 막을 이유가 없다 — 처음 만드는 사람이야말로 이
        도구가 필요한 사람이다.

        기본 선택은 **사용자가 답한 축마다 대표 재료 하나**다. 그래야 사용자가
        목표를 준 축을 하나도 빠짐없이 움직일 수 있는 배합에서 출발한다.
        슬롯마다 앞의 두 개를 집는 방식은 여기서 쓰지 않는다 — 어떤 축은
        재료가 하나도 없고 어떤 축은 셋씩 붙는다.

        반환: [{온톨로지ID, 재료, 슬롯, 등급, 하한, 상한, 범위근거, 담당축, 메모}]
        """
        eff = self.effects_for(profile)
        core = self.core_terms(profile)
        filler = self.filler_of(profile)

        # 축마다 대표 재료: 그 축을 가장 세게 움직이고, 겸사겸사 다른 축도
        # 건드리는 재료를 앞세운다. 재료 수가 적을수록 사용자가 읽기 쉽다.
        rep = {}
        for t in core:
            movers = [(g, e[t]) for g, e in eff.items() if t in e and g != filler]
            if not movers:
                continue
            # 곁가지가 **적은** 재료를 앞세운다. 반대로 두면 고추장처럼 여러
            # 축을 한꺼번에 건드리는 재료가 모든 축의 대표가 되어 버린다 —
            # 아이스크림 감미료가 고추장이 되는 식이다. 배합을 처음 잡을 때
            # 필요한 것은 축 하나에 레버 하나이고, 그래야 사용자가 슬라이더를
            # 움직였을 때 무엇이 왜 변했는지 읽힌다.
            movers.sort(key=lambda ge: (-ge[1]["mag"], len(eff[ge[0]]), ge[0]))
            rep[t] = movers[0][0]
        chosen = set(rep.values())

        # 축을 덮는 것만으로는 제형이 서지 않는다. 굴소스 하나가 걸쭉함·크리미함·
        # 코팅성을 다 건드린다고 해서 기름도 유화제도 없는 O/W 소스가 되지는
        # 않는다. 제형이 요구하는 기능군(STRUCTURE required_functions)에서는
        # 축 커버리지와 무관하게 대표를 하나씩 넣는다.
        req = []
        for sp in self._s_candidates(profile):
            req = sp.get("required_functions") or []
            if req:
                break
        for ft in req:
            if any(self.slot_of(g, profile)[0] == ft for g in chosen):
                continue
            pool = [g for g in eff
                    if g != filler and self.slot_of(g, profile)[0] == ft]
            if not pool:
                continue
            # 구조를 맡는 슬롯도 마찬가지로 전용에 가까운 재료가 낫다.
            # 다만 축을 하나도 안 움직이는 재료를 뽑으면 사용자가 조종할 수 없다.
            pool.sort(key=lambda g: (not [t for t in core if t in eff[g]],
                                     len([t for t in core if t in eff[g]]), g))
            chosen.add(pool[0])

        rows = []
        for g, e in sorted(eff.items()):
            if not e and g != filler:
                continue
            ft, slot = self.slot_of(g, profile)
            lo, hi, why = self.slot_bounds(profile, ft)
            # 이 범위는 **기능군 합계**다. 하한을 재료마다 걸면 같은 슬롯에서
            # 세 개를 고른 순간 하한이 세 배가 된다 — 아이스크림 지방 하한
            # 10% 가 재료 3종이면 30% 가 되는 식이다. 그래서 하한은 0 으로
            # 두고 근거 문구에만 남긴다. 상한은 재료 하나가 넘어설 수 없는
            # 선이므로 그대로 쓴다(합계로는 여전히 느슨한 근사다).
            if lo > 0:
                why = f"{why} (기능군 합계 {lo:g}~{hi:g}%)"
                lo = 0.0
            moves = [f"{self.label(t)}{'↑' if e[t]['sign'] > 0 else '↓'}"
                     for t in core if t in e]
            if g == filler:
                grade, lo, hi, why = "필수", 0.0, 100.0, "필러 — 나머지를 채운다"
                slot = "베이스"
            elif g in chosen:
                grade = "권장"
            else:
                grade = "옵션"
            rows.append(dict(
                온톨로지ID=g,
                재료=self.ing_label(g),
                슬롯=slot, 등급=grade, 하한=lo, 상한=hi, 범위근거=why,
                담당축=" ".join(moves), 메모="", 확인="온톨로지에서 자동"))
        return rows

    # ---------------------------------------------------------------- 감사
    def audit(self):
        """
        온톨로지 정합성 감사 — 스펙이 요구하지만 정본 로더가 구현하지 않은 검사들.

        loader_reference.py 는 스펙이 지정한 참조 구현이라 편집하지 않는다.
        그래서 빠진 검사를 여기에 둔다. 셋 다 "조용히 틀리는" 종류라서
        경고가 없으면 영영 안 보인다.

          1. direction 누락    필수 필드가 없으면 로더가 그 엣지를 건너뛴다.
                               오류도 경고도 없이 0 이 된다.
          2. R-1 액추에이터    스펙 §5.9: "액추에이터가 없는 R-1 레코드를
                               로더는 반드시 플래그해야 한다". 미구현이었다.
          3. 태그 불이행       FT.flavorant 는 효과 엣지를 갖지 않는 선언용
                               태그다. 향은 재료가 flavor_profile 로 직접
                               선언해야 하는데, 빠뜨리면 향미재가 향을 못 낸다.

        반환은 항목별 리스트. 비어 있으면 깨끗하다는 뜻이다.
        """
        out = dict(directionless=[], untagged=[], unfulfilled=[],
                   orphan_proxies={}, dead_core={}, unreachable_active=[])

        # --- 1) direction 누락
        for tid, t in self.tags.items():
            for e in (t.get("effects") or []):
                if "direction" not in e:
                    out["directionless"].append(
                        ("tag", tid, e.get("to"), e.get("scoped_to_structure_class")))
        for gid, g in self.ingredients.items():
            for key in ("overrides", "flavor_profile"):
                for e in (g.get(key) or []):
                    if "direction" not in e:
                        out["directionless"].append(
                            (key, gid, e.get("to"), e.get("scoped_to_structure_class")))

        # --- 3) 재료가 실제로 아무 효과도 내지 못하는 경우
        #
        # "function_tags 가 비었나" 가 아니라 "효과가 나오나" 를 본다. 태그로
        # 상속받든 overrides 로 직접 쓰든 결과가 같기 때문이다. 필드 유무를
        # 보면 alias_of 확장으로 고친 재료를 계속 결손으로 오인한다.
        all_eff = {}
        for prof in self.profiles:
            try:
                for g, e in self.effects_for(prof).items():
                    if e:
                        all_eff.setdefault(g, set()).update(e)
            except Exception:                                  # noqa: BLE001
                continue
        for gid, g in self.ingredients.items():
            if gid in all_eff:
                continue
            if gid == "ING.water":            # 필러는 비어 있는 것이 정상
                continue
            out["untagged"].append(gid)

        # FT.flavorant 는 선언용 태그다 — 향은 재료가 직접 줘야 한다.
        # 향 축(L.ar.*)을 하나도 움직이지 못하면 향미재 구실을 못 하는 것이다.
        for gid, g in self.ingredients.items():
            if "FT.flavorant" not in (g.get("function_tags") or []):
                continue
            aroma = {t for t in all_eff.get(gid, set()) if t.startswith("L.ar.")}
            if not aroma:
                out["unfulfilled"].append((gid, "FT.flavorant", "향 축을 하나도 움직이지 못함"))

        # --- 2) 프로파일별: 액추에이터 없는 R-1, 그리고 못 움직이는 core 축
        for prof in self.profiles:
            scopes = self.profiles[prof]["scopes"]
            moved = set()
            for _, t in self.tags.items():
                for e in (t.get("effects") or []):
                    sc = e.get("scoped_to_structure_class", "any")
                    sc = sc if isinstance(sc, list) else [sc]
                    if str(e.get("to", "")).startswith("P.") and e.get("direction")                             and any(x in scopes for x in sc):
                        moved.add(e["to"])
            for _, g in self.ingredients.items():
                for e in (g.get("overrides") or []):
                    sc = e.get("scoped_to_structure_class", "any")
                    sc = sc if isinstance(sc, list) else [sc]
                    if str(e.get("to", "")).startswith("P.") and e.get("direction")                             and any(x in scopes for x in sc):
                        moved.add(e["to"])
            refd = {r["parameter"] for r in self.stack["R"]["relations_proxy"]
                    if r["scope"] in scopes}
            orphan = sorted(refd - moved)
            if orphan:
                out["orphan_proxies"][prof] = orphan

            try:
                cards = self._ref.load_cards(prof, self.layers)
            except Exception:                                  # noqa: BLE001
                continue
            core = [c["term_id"] for c in cards if c["tier"] == "core"]
            # 활성 용어 전체의 도달성도 본다. 단 숙성 속성(sample_aged)은
            # 배합이 아니라 시간이 만드는 것이라 R-4 kinetics 로 다루는 것이
            # 맞다(스펙 5.8). R-4 가 덮고 있으면 결손이 아니다.
            r4 = {r.get("subject") or r.get("phenomenon")
                  for r in (self.stack["R"].get("relations_kinetics") or [])}
            for c in cards:
                t = c["term_id"]
                if any(t in self.effects_for(prof)[g] for g in self.effects_for(prof)):
                    continue
                if c.get("evidence_required") == "sample_aged" and t in r4:
                    continue                      # R-4 가 담당 — 정상
                out.setdefault("unreachable_active", []).append((prof, t, c["tier"]))
            eff = self.effects_for(prof)
            dead = [t for t in core if not any(t in eff[g] for g in eff)]
            if dead:
                out["dead_core"][prof] = dead
        return out

    def audit_report(self):
        """감사 결과를 사람이 읽는 줄글로."""
        a = self.audit()
        L = []
        L.append(f"direction 누락 엣지 {len(a['directionless'])}건 (조용히 0 이 된다)")
        for kind, owner, to, sc in a["directionless"]:
            L.append(f"    {kind:14s} {owner:30s} -> {str(to):28s} {sc}")
        L.append(f"function_tags 가 빈 재료 {len(a['untagged'])}종 (아무 축도 못 움직인다)")
        for g in a["untagged"]:
            L.append(f"    {g}")
        L.append(f"태그를 이행하지 않는 재료 {len(a['unfulfilled'])}건")
        for g, t, why in a["unfulfilled"]:
            L.append(f"    {g:34s} {t:18s} {why}")
        if a["orphan_proxies"]:
            L.append("액추에이터가 없는 R-1 (스펙 §5.9):")
            for p, xs in a["orphan_proxies"].items():
                L.append(f"    [{p}] {', '.join(xs)}")
        if a["dead_core"]:
            L.append("어떤 재료로도 못 움직이는 core 축:")
            for p, xs in a["dead_core"].items():
                L.append(f"    [{p}] {', '.join(xs)}")
        return chr(10).join(L)

    # ---------------------------------------------------------------- 조립
    def build(self, profile, palette, bounds=None, x0=None, total=100.0,
              sigma_from_cards=True):
        """
        palette : ING.* 목록. 필러가 없으면 자동으로 넣는다.
        bounds  : {ING.*: (lo, hi)} 재료별 작업 범위. zsd 와 propose 경계로 쓴다.
                  없는 재료는 x0 에서 추정하고 경고를 남긴다(온톨로지 G5 미해결분).
        x0      : 시작 배합(전체, 합계=total). 없으면 bounds 중앙값으로 만든다.
        """
        if profile not in self.profiles:
            raise KeyError(f"모르는 프로파일: {profile}. 가능: {list(self.profiles)}")
        filler = self.filler_of(profile)
        palette = list(palette)
        if filler not in palette:
            palette.append(filler)
        unknown = [g for g in palette if g not in self.stack["ings"]]
        if unknown:
            raise KeyError(f"온톨로지에 없는 재료: {unknown}")

        cards = self._ref.load_cards(profile, self.layers)
        asm = self._ref.assemble(profile, self.stack, cards, palette)
        y_terms = asm["y_terms"]
        if not y_terms:
            raise ValueError(f"프로파일 {profile} 의 core 반응축이 비었습니다")

        # --- 1) 필러 행 제거 (불변식 8)
        fi = palette.index(filler)
        keep = [j for j in range(len(palette)) if j != fi]
        if not keep:
            # 2026-09-11 검증 결함 12. 필러만 남으면 자유변수가 0개다. 여기서 안
            # 막으면 suggest() 가 scipy 에 빈 범위를 넘기고 scipy 안에서
            # "not enough values to unpack" 으로 터진다 - 뜻 모를 오류다.
            raise ValueError(
                f"팔레트에 필러 {filler} 말고 재료가 없습니다. 움직일 변수가 없어 "
                f"모형을 세울 수 없습니다 - 재료를 하나 이상 넣으세요.")
        G0 = asm["Gamma0"][keep, :]
        lam = asm["Lambda_per_edge"][keep, :]          # (q_free, m) 엣지별 유지
        free_names = [palette[j] for j in keep]

        warns = []
        # --- 2) 스케일. Γ₀ 는 1 SD 당이므로 재료 작업 범위에서 만든다.
        bounds = dict(bounds or {})
        zsd = np.empty(len(free_names))
        zbar = np.empty(len(free_names))
        no_range = []
        for i, g in enumerate(free_names):
            if g in bounds:
                lo, hi = float(bounds[g][0]), float(bounds[g][1])
                if hi <= lo:
                    raise ValueError(f"{g} 의 범위가 뒤집혔습니다: ({lo}, {hi})")
                if lo < 0:
                    # 2026-09-11 검증 결함 8. 음수 하한은 오타 말고는 나올 이유가
                    # 없고, 통과시키면 솔버가 음수 배합(-2.72%)을 낸다. "이 재료를
                    # 빼라" 는 뜻은 하한 0 이 이미 담는다 - 0 에 닿으면 다른 재료로
                    # 간다. (사용자: "원칙적으로 막아야 하는 부분")
                    raise ValueError(
                        f"{g} 의 하한이 음수입니다: {lo}. 재료 양은 0 아래로 못 "
                        f"갑니다 - 빼고 싶으면 하한을 0 으로 두세요.")
                zsd[i] = (hi - lo) / RANGE_TO_SD
                zbar[i] = 0.5 * (lo + hi)
            else:
                no_range.append(g)
                ref = abs(float(x0[palette.index(g)])) if x0 is not None else 0.0
                zsd[i] = max(ref, FALLBACK_SD)
                zbar[i] = ref
        zsd[zsd < 1e-9] = FALLBACK_SD
        if no_range:
            warns.append(
                f"작업 범위가 없어 임시 스케일을 쓴 재료 {len(no_range)}종: "
                f"{no_range[:6]}{'...' if len(no_range) > 6 else ''} — "
                f"온톨로지의 limitations 가 자유 서술이라 기계가 읽지 못한다(G5). "
                f"용량 상한표가 생기면 bounds 로 넘길 것.")

        # --- 3) 시작 배합
        if x0 is None:
            x0 = np.zeros(len(palette))
            for i, g in enumerate(free_names):
                x0[palette.index(g)] = zbar[i]
            rest = total - x0.sum()
            if rest < 0:
                # 작업 범위를 재료마다 따로 뽑으면(실측 min/max) 혼합물 제약을 모른다.
                # 서로 대체하는 재료 — 쌀시럽과 알룰로스처럼 한쪽이 높으면 다른 쪽이
                # 낮은 짝 — 은 각자의 중앙값이 동시에 성립하지 않는다. 그렇다고 범위가
                # 틀린 것은 아니다. 그래서 모두를 하한 쪽으로 **같은 비율만큼** 당겨
                # 실현 가능한 기준점을 잡는다. 각 재료는 제 범위 안에 그대로 있고,
                # 재료 사이의 크기 순서도 보존된다.
                lo_v = np.array([float(bounds[g][0]) if g in bounds else 0.0
                                 for g in free_names])
                cur = np.array([x0[palette.index(g)] for g in free_names])
                slack = cur - lo_v                     # 하한 위로 올라간 몫
                need = -rest + FILLER_HEADROOM
                if slack.sum() <= need:
                    raise ValueError(
                        f"작업 범위 하한의 합이 {lo_v.sum():.2f} 로 총량 {total} 에 "
                        f"너무 가깝습니다(필러 여유 {FILLER_HEADROOM}). 재료를 줄이거나 "
                        f"하한을 낮추세요.")
                over = -rest
                pull = need / slack.sum()
                cur = cur - slack * pull
                for i, g in enumerate(free_names):
                    x0[palette.index(g)] = cur[i]
                zbar = cur.copy()                      # 기준점이 곧 zbar 다
                rest = total - x0.sum()
                warns.append(
                    f"작업 범위 중앙값의 합이 총량을 {over:.2f} 넘어, 재료를 하한 쪽으로 "
                    f"{pull * 100:.0f}% 당겨 기준 배합을 잡았습니다. "
                    f"서로 대체하는 재료가 팔레트에 함께 있다는 뜻입니다 — "
                    f"범위는 재료마다 따로 뽑혀 혼합물 총량 제약을 모릅니다.")
            x0[fi] = rest
        else:
            x0 = np.asarray(x0, float)
            if abs(x0.sum() - total) > 1e-4:
                raise ValueError(f"x0 의 합계가 {x0.sum():.4f} 입니다. {total} 이어야 합니다.")

        # --- 4) Σ₀ (M 카드 reliability + R-2 상관)
        S0 = asm["Sigma0"] if sigma_from_cards else np.eye(len(y_terms))

        model = MixtureModel(palette, filler=filler, total=total)
        model.fit_prior_only(prior=G0, prior_precision=lam, sigma=S0,
                             zbar=zbar, zsd=zsd)

        per_axis = (G0 != 0).sum(axis=0)
        dead = [y_terms[k] for k in range(len(y_terms)) if per_axis[k] == 0]
        if dead:
            warns.append(
                f"이 팔레트로는 움직일 수 없는 축: {dead} — 목표에 넣어도 반응하지 않는다. "
                f"해당 축을 움직이는 재료를 팔레트에 넣거나 목표에서 빼세요(G2).")

        return BuiltModel(model=model, palette=palette, filler=filler,
                          y_terms=y_terms, Gamma0=G0, Lambda=lam, Sigma0=S0,
                          zsd=zsd, zbar=zbar, cards=asm["cards"], warnings=warns)

    # ---------------------------------------------------------------- 제안
    def suggest(self, built: BuiltModel, target, x0=None, bounds=None, **kw):
        """
        target : {L.* 축: 목표 변화량} 또는 길이 m 배열.
        bounds : {ING.*: (lo, hi)} — 넘기지 않으면 상한이 없어 물리적으로
                 불가능한 용량이 나올 수 있다(G5). 넘기면 그대로 경계가 된다.
        """
        m = built.model
        if isinstance(target, dict):
            t = np.zeros(len(built.y_terms))
            unknown = [k for k in target if k not in built.y_terms]
            if unknown:
                raise KeyError(f"이 프로파일의 축이 아닙니다: {unknown}. "
                               f"가능: {built.y_terms}")
            for k, v in target.items():
                t[built.y_terms.index(k)] = float(v)
        else:
            t = np.asarray(target, float)
        # 2026-09-11 검증 결함 9·10. 척도는 ±3 이다. 그 밖의 값은 뜻이 없고,
        # NaN 은 그 목표가 조용히 사라진다(빈 목표와 같은 배합이 나왔다).
        # 목표 입력 화면은 이미 ±2 로 막혀 있으니 여기 오는 것은 코드 경로뿐이다.
        # (사용자: "원칙적으로 막아야 하는 부분")
        if np.any(np.isnan(t)):
            bad = [built.y_terms[i] for i in np.where(np.isnan(t))[0]]
            raise ValueError(f"목표에 숫자가 아닌 값(NaN)이 있습니다: {bad}")
        if np.any(np.abs(t) > 3.0 + 1e-9):
            bad = [(built.y_terms[i], float(t[i])) for i in np.where(np.abs(t) > 3.0)[0]]
            raise ValueError(f"목표가 척도(±3)를 벗어났습니다: {bad}")

        if x0 is None:
            x0 = np.zeros(len(built.palette))
            for i, g in enumerate([n for n in built.palette if n != built.filler]):
                x0[built.palette.index(g)] = built.zbar[i]
            x0[built.palette.index(built.filler)] = m.total - x0.sum()

        free = [n for n in built.palette if n != built.filler]
        lo = hi = None
        if bounds:
            lo = np.array([float(bounds.get(g, (0.0, m.total))[0]) for g in free])
            hi = np.array([float(bounds.get(g, (0.0, m.total))[1]) for g in free])

        return propose(m, target=t, x0=np.asarray(x0, float), lo=lo, hi=hi, **kw)


# 비건·저당 완제 아이스크림(HANDOFF §3.3 트랙)의 작업 범위.
# 팔레트와 범위는 **도메인 지식**이지 온톨로지에서 유도되지 않는다. 온톨로지의
# limitations 가 자유 서술이라 기계가 못 읽기 때문이다(G5). 상한표가 생기면
# 이 딕셔너리가 그 표로 대체된다.
DEMO_ICECREAM = {
    "ING.rice_extract":        (12.0, 14.0),   # 필수. 저당 회계상 당류 공급원
    "ING.refined_coconut_oil": (6.0, 14.0),    # 정제야자유
    "ING.allulose":            (9.0, 15.0),    # 당류 미산입
    "ING.soy_protein_isolate": (1.0, 3.0),     # 쌀단백 아님(가용성 결론)
    "ING.guar_gum":            (0.15, 0.35),
    "ING.anyaddy_an15":        (0.10, 0.50),   # HPMC
}


def smoke(profile="icecream"):
    """정합성 확인용. python -m formulator.v2adapter 로 실행."""
    onto = V2Ontology()
    print(f"온톨로지 로드: 재료 {len(onto.ingredients)}종 · 태그 {len(onto.tags)}종")
    for prof in onto.profiles:
        print(f"  [{prof:22s}] 필러={onto.filler_of(prof):12s} "
              f"후보재료={len(onto.candidates(prof))}")

    if profile != "icecream":
        print(f"\n(데모 팔레트는 icecream 만 준비돼 있습니다)")
        return

    print(f"\n--- build: {profile} (비건·저당 완제 아이스크림)")
    bounds = DEMO_ICECREAM
    built = onto.build(profile, list(bounds), bounds=bounds)
    print(built.report())

    print(f"\n  시작 배합(범위 중앙값):")
    x0 = np.zeros(len(built.palette))
    for i, g in enumerate([n for n in built.palette if n != built.filler]):
        x0[built.palette.index(g)] = built.zbar[i]
    x0[built.palette.index(built.filler)] = built.model.total - x0.sum()
    for n, v in zip(built.palette, x0):
        print(f"     {n:32s} {v:7.2f}")
    y0 = built.model.predict(x0[None, :])[0]
    print(f"  예측 반응 {dict(zip(built.y_terms, np.round(y0, 2).tolist()))}")

    axis = "L.tx.creaminess" if "L.tx.creaminess" in built.y_terms else built.y_terms[0]
    print(f"\n  목표: {axis} +1.0 (나머지 유지)")
    x = onto.suggest(built, {axis: 1.0}, x0=x0, bounds=bounds)
    for n, a, b in zip(built.palette, x0, x):
        mark = "  <-" if abs(b - a) > 0.05 else ""
        print(f"     {n:32s} {a:7.2f} -> {b:7.2f}{mark}")
    print(f"  합계 {x.sum():.4f}")
    y1 = built.model.predict(x[None, :])[0]
    print(f"  예측 반응 {dict(zip(built.y_terms, np.round(y1, 2).tolist()))}")

    # B1 이 살아 있는지 — 관능 예측이 척도 안에 머무는가
    if np.abs(y1).max() > 3.0:
        print(f"\n  !! 예측이 ±3 척도를 벗어났습니다({np.abs(y1).max():.1f}). "
              f"스케일(zsd)을 확인하세요.")
    else:
        print(f"\n  예측이 ±3 관능 척도 안에 머뭅니다(최대 {np.abs(y1).max():.2f}).")


if __name__ == "__main__":
    smoke(sys.argv[1] if len(sys.argv) > 1 else "icecream")
