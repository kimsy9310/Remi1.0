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

from .mixture import MixtureModel, propose


# 이 파일 기준: engine/formulator/v2adapter.py → 프로젝트 루트는 두 단계 위
_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT = os.path.abspath(os.path.join(_HERE, "..", ".."))
DEFAULT_ROOT = os.path.join(_PROJECT, "ontology_v2")

# 작업 범위를 모를 때 쓰는 임시 스케일 규칙(폭/4 ≈ 1 SD 로 보는 것)
RANGE_TO_SD = 4.0
FALLBACK_SD = 0.5          # 범위도 x0 도 없을 때의 최후 기본값

# 제품 단위로 얹는 프로파일(스펙 F7). 정체성은 SC×APP×ST 뿐이라 "제품" 차원이
# 없으므로, 제품별 M 카드를 상위 프로파일 위에 레이어링한다. coffee_milk 가
# 선례이고 rice_milk 가 같은 방식이다.
#
# 정본 로더(tests/loader_reference.py)의 PROFILES 를 **편집하지 않는다** —
# 그 파일은 스펙이 지정한 참조 구현이라 그대로 둬야 갱신본을 받을 수 있다.
# 대신 여기서 병합한다.
EXTRA_PROFILES = {
    "beverage_rice_milk": dict(
        cards=["layerM_cards_beverage_rice_milk.yaml"],
        scopes={"any", "SC.emulsion.ow", "SC.emulsion.ow.beverage",
                "SC.emulsion.ow|APP.beverage"}),
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
        # 정본 로더의 PROFILES + 제품 단위 확장(F7). 원본은 그대로 둔다.
        self.profiles = {**self._ref.PROFILES, **EXTRA_PROFILES}
        self._ref.PROFILES = self.profiles      # validate/assemble 도 같은 표를 보게

    # ---------------------------------------------------------------- 조회
    @property
    def ingredients(self):
        return self.stack["ings"]

    @property
    def tags(self):
        return self.stack["tags"]

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
        beverage_coffee_milk 처럼 제품 단위로 얹은 프로파일은 자기 S 항목이
        없고 상위(beverage)의 것을 쓴다(F7).
        """
        scopes = self.profiles[profile]["scopes"]
        out = []
        for sp in self.stack["S"]:
            parts = [sp.get("structure_class"), sp.get("application"), sp.get("state")]
            ident = "|".join(p for p in parts if p)
            if ident in scopes or sp.get("structure_class") in scopes:
                out.append(sp)
        # 더 구체적인 정체성을 먼저 (아이스크림이 음료보다 앞서야 한다)
        out.sort(key=lambda sp: -sum(1 for p in (sp.get("structure_class"),
                                                 sp.get("application"),
                                                 sp.get("state")) if p))
        return out

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
                raise ValueError(
                    f"작업 범위 중앙값의 합이 {x0.sum():.2f} 로 총량 {total} 을 넘습니다. "
                    f"팔레트를 줄이거나 범위를 낮추세요.")
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
