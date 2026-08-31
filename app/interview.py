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


def axis_label(term_id):
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
                product = ((d or {}).get("meta") or {}).get("product")
                if product:
                    break
            n_core = sum(1 for c in cards if c["tier"] == "core")
        except Exception:                                      # noqa: BLE001
            n_core = 0
        n_ing = None
        if load_palette is not None:
            try:
                t = load_palette(prof, None)
                n_ing = len([r for r in t.rows if r["등급"] != "제외"]) if t else 0
            except Exception:                                  # noqa: BLE001
                n_ing = 0
        out.append(dict(
            profile=prof,
            label=(product or sp.get("label") or prof).split("(")[0].strip(),
            definition=(sp.get("definition") or "").strip(),
            boundary=(sp.get("boundary_note") or "").strip(),
            n_core=n_core,
            n_ing=n_ing,
            ready=(n_ing is None or n_ing > 0),
            is_product=bool(product)))
    # 준비된 제품을 먼저, 그중 제품 단위를 먼저
    out.sort(key=lambda d: (not d["ready"], not d["is_product"], d["label"]))
    return out


# ---------------------------------------------------------------- ② 목표
def goal_questions(onto, profile):
    """
    core 축마다 질문 하나. 보기 문구는 M 카드의 anchors 를 쓴다 —
    평가자에게 실제로 전달되는 정의가 거기 있기 때문이다.
    """
    cards = onto._ref.load_cards(profile, onto.layers)
    qs = []
    for c in cards:
        if c["tier"] != "core" or c.get("evidence_required") == "sample_aged":
            continue
        # anchors 가 dict 인 카드도 list 인 카드도 있다. 둘 다 받는다.
        raw = c.get("anchors")
        anch = raw if isinstance(raw, dict) else {}
        opts = []
        for v in STEPS:
            key = {-2.0: "-3", 2.0: "+3", 0.0: "0"}.get(v)
            txt = str(anch.get(key, "")).strip() if (key and anch) else ""
            opts.append(dict(value=v, label=STEP_LABEL[v], detail=txt))
        qs.append(dict(
            term=c["term_id"],
            label=axis_label(c["term_id"]),
            goal=c.get("default_goal"),
            hint=GOAL_HINT.get(c.get("default_goal"), ""),
            note=(c.get("evaluation_note") or "").strip(),
            pitfalls=c.get("pitfalls") or [],
            reliability=c.get("reliability"),
            options=opts))
    return qs


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
            moves = [f"{axis_label(t)}{'↑' if e[t]['sign'] > 0 else '↓'}"
                     for t in core if t in e]
            items.append(dict(
                id=g, label=r["재료"] or g.replace("ING.", ""),
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
                f"**{axis_label(t)}** 를 움직일 재료가 고른 것 중에 없습니다. "
                f"그 축은 목표로 줘도 반응하지 않습니다.")

    if ptab is not None:
        b = ptab.bounds(include_restricted=True)
        nob = [g for g in pal if g not in b and g != filler]
        if nob:
            msgs.append(
                f"작업 범위가 없는 재료 {len(nob)}종이 있습니다 — "
                f"제안이 물리적으로 불가능한 값을 낼 수 있습니다: "
                f"{[g.replace('ING.', '') for g in nob[:5]]}")
    return msgs
