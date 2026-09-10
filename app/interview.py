# -*- coding: utf-8 -*-
"""
사용자 인터뷰 — v2 온톨로지에서 질문을 직접 만든다.

왜 질문을 코드에 박지 않나
--------------------------
질문 목록을 손으로 관리하면 온톨로지가 바뀔 때마다 어긋난다. 옛 프로토타입의
질문 은행 235개가 그렇게 됐다 — v1 시절 이름(P.aftertaste_length 등)으로 쓰여
있는데 v2 는 그중 상당수를 관능(L.*)으로 옮겼다. 28종 중 4종만 이름이 맞는다.

그래서 여기서는 **질문을 온톨로지에서 생성한다.**

    S 프로파일  ->  "무엇을 만드시나요"   (제형 정의·경계 설명)
    M 카드      ->  "무엇을 바꾸고 싶나요" (core 축 · anchors · default_goal)
    팔레트      ->  "무엇을 쓰시나요"      (슬롯별 재료 · 등급)

무엇을 물을지도 카드가 정한다
-----------------------------
카드가 있다고 다 묻지는 않는다. tier 와 default_goal 을 읽어 정체성 축·조절 축·
결함 축으로 나누고, 셋을 화면에서 다르게 다룬다 — `scope()` 가 그 규칙이다.

카드를 고치면 질문이 따라온다. 새 제품을 붙이면 질문이 저절로 생긴다.

기준 제품이 필요한 이유
-----------------------
모형의 관능 척도는 **벤치마크 상대**다(0 = 기준과 같음). 그런데 처음 만드는
사람에게는 기준이 없다. 그래서 인터뷰 첫머리에 "무엇과 비슷하게, 어디를 다르게"
를 묻는다. 사용자가 아는 시판 제품이 기준이 되고, 그 뒤 질문은 전부 "그것보다
더/덜" 이 된다 — 모형이 쓰는 좌표와 정확히 같아진다.
"""
from __future__ import annotations

from dataclasses import dataclass, field


# 목표 축 질문의 보기. M 카드의 anchors 가 있으면 그 문장을 쓰고,
# 없으면 아래 기본 문구로 채운다.
STEPS = [-2.0, -1.0, 0.0, 1.0, 2.0]
STEP_LABEL = {
    -2.0: "많이 덜하게", -1.0: "조금 덜하게", 0.0: "기준과 같게",
    1.0: "조금 더", 2.0: "많이 더",
}
# 정체성 축은 "바꿀까 말까" 가 아니라 "얼마나 강하게" 다. 눈금은 같은 −2…+2 이고
# 부르는 말만 다르다 — 매운 소스를 만들기로 이미 정했으니 물을 것은 세기뿐이다.
STRENGTH_LABEL = {
    -2.0: "많이 약하게", -1.0: "조금 약하게", 0.0: "기준만큼",
    1.0: "조금 강하게", 2.0: "많이 강하게",
}

GOAL_HINT = {
    "maintain": "기준과 같게 두는 것이 보통입니다",
    "increase": "올리는 쪽이 대개 목표입니다",
    "decrease": "낮추는 쪽이 대개 목표입니다",
    "target": "제품 성격을 정하는 축입니다 — 높낮이보다 '어디에 맞출까'입니다",
    "minimize": "결함 축입니다. 낮을수록 좋습니다",
}


# build_palette 가 실측에서 팔레트를 만들 때 붙이는 표시. 역할이 아직 안 나뉜
# 상태라는 뜻이라, 재료 기본 선택을 다르게 다뤄야 한다.
UNSLOTTED = {"(실측에서 자동)", "(미분류)"}


def _name(onto, ing_id, table_name):
    """
    재료 표시 이름.

    팔레트 표의 '재료' 열은 사람이 고칠 수 있는 칸이라 손으로 적은 이름이
    있으면 그것을 존중한다. 다만 실측에서 자동으로 만든 행은 영문 ID 가 그대로
    들어가 있어서, 한글이 한 글자도 없으면 온톨로지의 한글 이름으로 바꾼다.
    """
    t = str(table_name or "").strip()
    if t and any("가" <= c <= "힣" for c in t):
        return t
    try:
        return onto.ing_label(ing_id)
    except Exception:                                          # noqa: BLE001
        return t or ing_id.replace("ING.", "")


def axis_label(term_id, onto=None):
    """축의 표시 이름. 온톨로지를 주면 LEXICON 의 한글 이름을 쓴다."""
    if onto is not None:
        return onto.label(term_id)
    return term_id.split(".")[-1]


@dataclass
class Interview:
    """인터뷰 한 건의 상태. 앱이 세션에 들고 다닌다."""
    profile: str = None
    variant: str = None
    benchmark: str = ""              # 사용자가 말한 기준 제품
    goals: dict = field(default_factory=dict)     # {L.*: 목표값}
    free_axes: list = field(default_factory=list)  # 신경 쓰지 않는 축
    chosen: dict = field(default_factory=dict)     # {슬롯: [ING.*]}
    # ① 에서 확인한 "이 제품을 정하는 것". None 이면 아직 확인 전이라는 뜻이고,
    # 그때는 제형의 기본값(core + default_goal:target)을 쓴다.
    identity_axes: list = None
    changed: list = field(default_factory=list)    # ② 에서 바꾸겠다고 고른 축
    concerns: list = field(default_factory=list)   # ② 에서 신경 쓰인다고 고른 결함 축

    def reset_answers(self):
        """제품이 바뀌면 축도 재료도 갈린다. 앞서 받은 답을 버린다."""
        self.goals, self.chosen, self.free_axes = {}, {}, []
        self.identity_axes, self.changed, self.concerns = None, [], []

    def palette(self):
        out = []
        for gs in self.chosen.values():
            for g in gs:
                if g not in out:
                    out.append(g)
        return out

    def ready(self):
        return bool(self.profile and self.palette())


# ---------------------------------------------------------------- ① 제형
def product_choices(onto, load_palette=None):
    """
    S 프로파일을 '무엇을 만드나' 보기로. 제품 단위 프로파일(F7)이 있으면
    그쪽을 앞세운다 — 사용자에게는 '쌀 우유' 가 'O/W 에멀전 음료' 보다 가깝다.

    load_palette 를 주면 재료 표가 있는 제품인지도 함께 본다. 표가 없는 제품을
    고르면 ③ 단계가 빈 화면이 되므로, 고르기 전에 알려주는 편이 낫다.
    """
    out = []
    for prof in sorted(onto.profiles):
        sp = None
        try:
            cand = onto._s_candidates(prof)
            sp = cand[0] if cand else None
        except Exception:                                      # noqa: BLE001
            pass
        if not sp:
            continue
        product = None
        try:
            cards = onto._ref.load_cards(prof, onto.layers)
            # 제품 단위 카드 파일의 meta.product 를 쓰면 이름이 훨씬 친근하다
            import yaml
            import os
            for fn in onto.profiles[prof]["cards"]:
                d = yaml.safe_load(open(os.path.join(onto.layers, fn), encoding="utf-8"))
                meta = (d or {}).get("meta") or {}
                product = meta.get("product_ko") or meta.get("product")
                if product:
                    break
            n_core = sum(1 for c in cards if c["tier"] == "core")
        except Exception:                                      # noqa: BLE001
            n_core = 0
        sko = sp.get("ko") or {}
        n_ing = None
        if load_palette is not None:
            try:
                t = load_palette(prof, None)
                n_ing = len([r for r in t.rows if r["등급"] != "제외"]) if t else 0
            except Exception:                                  # noqa: BLE001
                n_ing = 0
        out.append(dict(
            profile=prof,
            label=(product or sko.get("label") or sp.get("label")
                   or prof).split("(")[0].strip(),
            definition=(sko.get("definition") or sp.get("definition") or "").strip(),
            boundary=(sko.get("boundary_note") or sp.get("boundary_note") or "").strip(),
            n_core=n_core,
            n_ing=n_ing,
            ready=(n_ing is None or n_ing > 0),
            is_product=bool(product)))
    # 준비된 제품을 먼저, 그중 제품 단위를 먼저
    out.sort(key=lambda d: (not d["ready"], not d["is_product"], d["label"]))
    return out


# ---------------------------------------------------------------- ② 목표
def _question(onto, card):
    """
    M 카드 한 장 → 질문 하나. 보기 문구는 카드의 anchors 를 쓴다 —
    평가자에게 실제로 전달되는 정의가 거기 있기 때문이다.
    """
    # 한글 블록이 있으면 그것을 쓴다. 평가자에게 그대로 읽히는 문장이라
    # 화면에는 한글이 정본이고, 영문은 온톨로지의 원문으로 남는다.
    ko = card.get("ko") or {}
    # anchors 가 dict 인 카드도 list(강도 기준점) 인 카드도 있다. 뜻이 아예
    # 다르므로 -3/0/+3 형태인 dict 만 앵커로 받는다.
    raw = ko.get("anchors") or card.get("anchors")
    anch = raw if isinstance(raw, dict) else {}
    opts = []
    for v in STEPS:
        key = {-2.0: "-3", 2.0: "+3", 0.0: "0"}.get(v)
        txt = str(anch.get(key, "")).strip() if (key and anch) else ""
        opts.append(dict(value=v, label=STEP_LABEL[v],
                         strength=STRENGTH_LABEL[v], detail=txt))
    return dict(
        term=card["term_id"],
        label=axis_label(card["term_id"], onto),
        goal=card.get("default_goal"),
        hint=GOAL_HINT.get(card.get("default_goal"), ""),
        note=(ko.get("evaluation_note") or card.get("evaluation_note") or "").strip(),
        pitfalls=ko.get("pitfalls") or card.get("pitfalls") or [],
        target=(ko.get("jar_target") or card.get("jar_target") or "").strip(),
        reliability=card.get("reliability"),
        options=opts)


def scope(onto, profile):
    """
    B1 `SCOPE` — 이 제형에서 **무엇을 물을지** 정한다.

    질문 은행은 이미 M 카드 70장이다. 없던 것은 어떤 조합을 물을지 정하는
    규칙이고, 그게 이 함수다. 판정 근거는 전부 카드 안에 있다.

        tier: monitored            안 묻는다. 사람이 답할 축이 아니다
        evidence_required:         안 묻는다. 저장 시험이 있어야 답이 나온다
          sample_aged               (스펙 5.8 격리)
        default_goal: target       **정체성 축.** 무엇을 만드는지가 이미 정해 준다.
                                   ① 에서 칩으로 확인하고 ② 에서는 세기만 묻는다
        default_goal: minimize     **결함 축.** 먼저 묻지 않는다. "신경 쓰이는
                                   것이 있나요" 로 접어 두고, 고른 것만 묻는다
        나머지(maintain/increase/  **조절 축.** 칩으로 바꿀 것을 먼저 고르게 하고,
          decrease)                고른 것에만 슬라이더를 붙인다

    되돌려 주는 것: identity / adjust / defect 세 묶음과, 안 묻기로 한 skipped.
    합치면 모형의 반응축(y_terms)과 정확히 같다 — 셋 다 core 이고 격리가 아니다.

    왜 이렇게 나누나. 현탁액을 고르면 지금은 슬라이더 10개가 한 번에 뜨고 그중
    다섯이 매운맛·건고추 향 같은 "이 제품이 무엇인가" 축이다. 이미 매운 소스를
    만들기로 하고 들어온 사람에게 매운맛을 0 에 둘지 묻는 것은 질문이 아니다.
    """
    out = dict(identity=[], adjust=[], defect=[], skipped=[])
    for c in onto._ref.load_cards(profile, onto.layers):
        if c["tier"] != "core":
            out["skipped"].append(dict(term=c["term_id"], why="monitored"))
            continue
        if c.get("evidence_required") == "sample_aged":
            out["skipped"].append(dict(term=c["term_id"], why="sample_aged"))
            continue
        q = _question(onto, c)
        goal = c.get("default_goal")
        out["identity" if goal == "target"
            else "defect" if goal == "minimize"
            else "adjust"].append(q)
    return out


def goal_questions(onto, profile):
    """물을 수 있는 축 전부. scope() 의 세 묶음을 이어 붙인 것이다."""
    sc = scope(onto, profile)
    return sc["identity"] + sc["adjust"] + sc["defect"]


def default_identity(onto, profile):
    """이 제형이 기본으로 내세우는 정체성 축. ① 칩의 초기값."""
    return [q["term"] for q in scope(onto, profile)["identity"]]


def identity_candidates(onto, profile):
    """
    ① 의 '이 제품을 정하는 것' 칩에 더할 수 있는 축.

    후보는 렉시콘의 향(`L.ar.*`)과 화학감각(`L.ch.*`) 134개다. 제품의 정체성을
    지는 것은 대개 이 둘이고, 단맛·걸쭉함 같은 축은 정체성이 아니라 조절 대상이라
    ② 에 남는다.

    이 제형의 core 카드로 있는 축만 모형이 실제로 움직일 수 있다(`modeled`).
    나머지는 골라도 기록으로만 남는다 — 그래도 후보에서 빼지 않는다. 현탁액
    카드에 박혀 있는 "건고추 향·장 발효 향" 은 이 제형이 발효 핫소스여야 한다는
    뜻이 아니라 기본값일 뿐이고("Swappable"), 토마토 살사를 만들려는 사람은
    그 자리에 다른 향을 적을 수 있어야 한다.
    """
    modeled = set(onto.core_terms(profile))
    # 이 제형이 이미 정체성으로 세운 축은 접두사와 무관하게 후보다. 커피우유의
    # 쓴맛(L.ta.*)과 현탁액의 감칠맛이 그렇다 — 빼면 기본값이 후보에 없어
    # 화면에 그리는 순간 사라진다.
    seed = set(default_identity(onto, profile))
    out = []
    for t in list(onto.stack["lex"]) + sorted(seed - set(onto.stack["lex"])):
        if not (t.startswith("L.ar.") or t.startswith("L.ch.") or t in seed):
            continue
        out.append(dict(term=t, label=axis_label(t, onto), modeled=t in modeled))
    out.sort(key=lambda d: (not d["modeled"], d["label"]))
    return out


# ---------------------------------------------------------------- ③ 재료
def ingredient_questions(ptab, onto, profile):
    """
    슬롯별로 '무엇을 쓰시나요'. 슬롯 하나가 모형의 변수 하나이므로
    슬롯 단위로 묻는 것이 팔레트 설계와도 맞는다.
    """
    if ptab is None:
        return []
    eff = onto.effects_for(profile)
    cards = onto._ref.load_cards(profile, onto.layers)
    core = [c["term_id"] for c in cards
            if c["tier"] == "core" and c["evidence_required"] != "sample_aged"]

    by_slot = {}
    for r in ptab.rows:
        if r["등급"] in ("제외",):
            continue
        by_slot.setdefault(r["슬롯"] or "(미분류)", []).append(r)

    out = []
    for slot, rows in by_slot.items():
        # 슬롯이 나뉜 팔레트에서 기본 2종은 "같은 역할끼리 경쟁하니 대표만" 이라는
        # 뜻이다. 슬롯이 없는 팔레트(실측에서 자동 생성)에는 그 경쟁 구조가 없어
        # 앞의 2종을 집으면 그냥 알파벳순 아무거나가 된다. 그때는 전부 켠다.
        unslotted = slot in UNSLOTTED
        rows.sort(key=lambda r: {"필수": 0, "권장": 1, "옵션": 2, "제한": 3}.get(r["등급"], 4))
        items = []
        for r in rows:
            g = r["온톨로지ID"]
            e = eff.get(g) or {}
            moves = [f"{axis_label(t, onto)}{'↑' if e[t]['sign'] > 0 else '↓'}"
                     for t in core if t in e]
            items.append(dict(
                id=g, label=_name(onto, g, r["재료"]),
                grade=r["등급"], moves=moves,
                bounds=(r["하한"], r["상한"]),
                memo=r["메모"], why=r["범위근거"]))
        must = any(r["등급"] == "필수" for r in rows)
        pick = [i["id"] for i in items if i["grade"] in ("필수", "권장")]
        out.append(dict(slot=slot, items=items, required=must,
                        unslotted=unslotted,
                        default=pick if unslotted else pick[:2]))
    # 필수 슬롯을 먼저
    out.sort(key=lambda d: (not d["required"], d["slot"]))
    return out


# ---------------------------------------------------------------- 점검
def check(onto, iv, ptab):
    """제안 직전 점검. 사용자에게 보여줄 말로."""
    msgs = []
    if not iv.profile:
        return ["만들 제품을 먼저 골라주세요."]
    pal = iv.palette()
    if not pal:
        return ["쓸 재료를 하나 이상 골라주세요."]

    filler = onto.filler_of(iv.profile)
    if filler not in pal:
        pal = pal + [filler]

    eff = onto.effects_for(iv.profile)
    for t, v in iv.goals.items():
        if t in iv.free_axes or abs(v) < 1e-9:
            continue
        movers = [g for g in pal if t in (eff.get(g) or {})]
        if not movers:
            msgs.append(
                f"**{axis_label(t, onto)}** 를 바꿀 수 있는 재료가 고른 것 중에 "
                f"없습니다. ③ 으로 돌아가 재료를 더 고르시면 반영됩니다.")

    # 사용 범위가 없는 재료는 이제 나오지 않는다(온톨로지가 기능군 통상 사용량을
    # 채운다). 그래도 표를 손으로 고쳐 비워 둔 경우가 있어 남겨 둔다.
    if ptab is not None:
        b = ptab.bounds(include_restricted=True)
        nob = [g for g in pal if g not in b and g != filler]
        if nob:
            names = ", ".join(g.replace("ING.", "") for g in nob[:4])
            msgs.append(
                f"쓰는 양의 범위가 정해지지 않은 재료가 있습니다({names}). "
                f"제안에 나온 양이 실제로 쓸 수 있는 양인지 확인해 주세요.")
    return msgs
