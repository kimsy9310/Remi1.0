# -*- coding: utf-8 -*-
"""
축 의존성 감사 — 어떤 축이 제형에 걸리고 어떤 축이 안 걸리나 (착수 순서 1.8).

왜 필요한가
-----------
아이스크림에 짠맛 카드가 없었다. 그런데 `ING.salt` 는
`scoped_to_structure_class: any` 로 짠맛 엣지를 갖고 있었다 — **엔진은 소금이
짜다는 것을 알면서 물어보지 못했다.** 2026-09-07 에 기본맛 6축은 열었지만,
같은 함정이 나머지 210개 축에 그대로 남아 있다.

원인은 세 질문이 하나로 뭉개진 것이다.

    이 감각이 존재하나        -> 물리적 전제.  제형에 걸릴 수도 아닐 수도
    여기서 어떻게 재나        -> M 카드.       제형에 걸린다
    여기서 최적화 대상인가    -> tier.         제형에 걸린다

첫 줄의 답을 **카드 유무로** 하고 있었다. 카드는 누가 썼느냐의 기록이다.

이 도구가 하는 일
-----------------
신호 두 개를 제형 × 축으로 교차시켜 **어긋나는 칸**을 찾는다.

    B  움직일 수 있나   재료가 이 축에 닿는 엣지를 갖고 있나 (R-1 합성 포함)
    C  물어보나         이 제형에 이 축의 M 카드가 있나

| B | C | 뜻 |
|---|---|---|
| O | O | 정상 |
| **O** | **X** | **움직일 수 있는데 안 묻는다** — 짠맛이 있던 자리 |
| X | O | 카드는 있는데 못 움직인다 (core 면 불변식 6 위반) |
| X | X | 정상. 선반 재고 |

세 번째 신호인 **물리적 전제(`requires`)는 아직 없다.** 일부러 그렇게 했다 —
미리 써 놓고 감사하면 내가 쓴 것을 내가 확인하는 꼴이 된다. 대신 이 도구가
"전 제형에서 못 움직이는 축" 을 뽑아 주면 그것이 `requires` 초안의 입력이 된다.

    python tools/audit_axis_scope.py            # 보고서
    python tools/audit_axis_scope.py --xlsx     # 검토표까지 (data/axis_review.xlsx)

자세한 배경: docs/축_의존성_검증전략.md
"""
from __future__ import annotations

import collections
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(HERE, "engine")]

from formulator.v2adapter import V2Ontology            # noqa: E402

OUT_XLSX = os.path.join(HERE, "data", "axis_review.xlsx")

# 도메인별 예상. 감사가 이것을 뒤집으면 그 자체가 발견이다.
DOMAIN = {
    "ta": ("맛", "보편 — 수용체 수준"),
    "ch": ("화학감각", "보편으로 예상 — 작열은 매트릭스와 무관"),
    "ar": ("향", "제품이 정한다 — 제형 무관. 제품 사전이 다룰 몫"),
    "tx": ("식감", "갈린다 — 여기가 작업의 본체"),
    "ap": ("외관", "갈린다"),
}


def collect(onto):
    """제형 × 축으로 B(움직일 수 있나) 와 C(카드 있나) 를 모은다."""
    profiles = sorted(onto.profiles)
    movable, carded, tier = {}, {}, {}
    for p in profiles:
        eff = onto.effects_for(p)
        m = set()
        for g, e in eff.items():
            m |= set(e)
        movable[p] = m
        cs = onto._ref.load_cards(p, onto.layers)
        carded[p] = {c["term_id"] for c in cs}
        tier[p] = {c["term_id"]: c["tier"] for c in cs}
    return profiles, movable, carded, tier


def main(want_xlsx=False):
    onto = V2Ontology()
    lex = onto.stack["lex"]
    profiles, movable, carded, tier = collect(onto)
    P = len(profiles)

    # ---------------------------------------------------------- 4분면
    quad = collections.Counter()
    ask_gap = collections.defaultdict(list)     # 움직일 수 있는데 안 묻는다
    dead_card = collections.defaultdict(list)   # 카드는 있는데 못 움직인다
    for p in profiles:
        for t in lex:
            b, c = t in movable[p], t in carded[p]
            quad[(b, c)] += 1
            if b and not c:
                ask_gap[t].append(p)
            if c and not b:
                dead_card[t].append((p, tier[p][t]))

    print("=" * 74)
    print("  축 의존성 감사 — 제형 × 축")
    print("=" * 74)
    print(f"\n프로파일 {P}개 × 렉시콘 {len(lex)}개 = {P*len(lex):,} 칸\n")
    print(f"  {'움직임':<6} {'카드':<6} {'칸':>7}   뜻")
    for (b, c), n in sorted(quad.items(), key=lambda kv: -kv[1]):
        mean = {(True, True): "정상",
                (True, False): "★ 움직일 수 있는데 안 묻는다",
                (False, True): "카드는 있는데 못 움직인다",
                (False, False): "정상 (선반 재고)"}[(b, c)]
        print(f"  {'O' if b else 'X':<6} {'O' if c else 'X':<6} {n:>7,}   {mean}")

    # ---------------------------------------------- ① 물어볼 수 있는데 안 묻는다
    print("\n" + "-" * 74)
    print("① 움직일 수 있는데 안 묻는 축 — 짠맛이 있던 자리")
    _ar = sum(len(ps) for t, ps in ask_gap.items() if t.startswith("L.ar."))
    _gap = quad[(True, False)]
    print(f"    ★ {_gap:,} 칸 중 향(L.ar)이 {_ar:,} 칸이다. 향은 제형이 아니라 제품이")
    print(f"    정하므로 제품 사전이 켤 몫이고 결함이 아니다.")
    print(f"    실제로 볼 것은 나머지 {_gap - _ar:,} 칸이다.")
    print("-" * 74)
    by_dom = collections.defaultdict(list)
    for t, ps in ask_gap.items():
        by_dom[t.split(".")[1]].append((len(ps), t, ps))
    for d in ("ta", "ch", "tx", "ap", "ar"):
        rows = sorted(by_dom.get(d, []), reverse=True)
        if not rows:
            continue
        ko, note = DOMAIN[d]
        full = [r for r in rows if r[0] == P]
        print(f"\n  L.{d} {ko}  —  {len(rows)}개 축 "
              f"(그중 {len(full)}개는 전 제형에서)   〔{note}〕")
        for n, t, ps in rows[:8]:
            # n 은 '움직이는데 안 묻는' 제형 수다. 움직이는 제형 수와 다르다 —
            # 크리미함은 5곳에서 움직이고 3곳에 카드가 있어 여기서는 2 로 나온다.
            mv = sum(1 for q in profiles if t in movable[q])
            where = "전 제형" if n == P else f"{n}곳 (움직임 {mv}/{P})"
            print(f"     {onto.label(t):<18} {t:<30} {where}")
        if len(rows) > 8:
            print(f"     … 그 밖 {len(rows)-8}개")

    # ---------------------------------------------- ② 카드는 있는데 못 움직인다
    print("\n" + "-" * 74)
    print("② 카드는 있는데 못 움직이는 축")
    print("-" * 74)
    if not dead_card:
        print("  없음")
    for t, pts in sorted(dead_card.items()):
        core = [p for p, ti in pts if ti == "core"]
        mon = [p for p, ti in pts if ti != "core"]
        mark = "  ‼ core — 불변식 6 위반" if core else "  (monitored — 합법이나 조종 불가)"
        print(f"  {onto.label(t):<18} {t:<30}{mark}")
        if core:
            print(f"       core: {core}")
        if mon:
            print(f"       monitored: {mon}")

    # ---------------------------------------------- ③ requires 초안 후보
    print("\n" + "-" * 74)
    print("③ `requires` 초안 후보 — 제형마다 움직임이 갈리는 축")
    print("-" * 74)
    print("  전 제형에서 움직이면 물리적 전제가 없다는 뜻이고, 일부에서만")
    print("  움직이면 전제가 있거나 엣지가 덜 쓰인 것이다. 둘을 가르는 것이")
    print("  다음 단계의 일이다.\n")
    split = []
    for t in lex:
        ps = [p for p in profiles if t in movable[p]]
        if 0 < len(ps) < P:
            split.append((len(ps), t, ps))
    split.sort(reverse=True)
    print(f"  갈리는 축 {len(split)}개\n")
    for n, t, ps in split:
        if t.split(".")[1] == "ar" and n < 3:
            continue                      # 향은 제품이 정한다. 여기서 볼 것이 아니다
        short = [p.replace("beverage_", "b_").replace("suspension_", "s_") for p in ps]
        print(f"     {onto.label(t):<18} {t:<30} {n}/{P}  {short}")

    # ---------------------------------------------- ④ 전 제형에서 못 움직임
    never = [t for t in lex if not any(t in movable[p] for p in profiles)]
    print("\n" + "-" * 74)
    print(f"④ 어느 제형에서도 못 움직이는 축 {len(never)}개")
    print("-" * 74)
    print("  선반 재고다. 결함이 아니지만, 카드를 붙이려면 먼저 엣지가 필요하다.")
    dn = collections.Counter(t.split(".")[1] for t in never)
    for d in ("ar", "tx", "ap", "ta", "ch"):
        if dn.get(d):
            print(f"     L.{d} {DOMAIN[d][0]:<8} {dn[d]:>3}개")

    if want_xlsx:
        write_review(onto, profiles, movable, carded, tier, ask_gap, split)
    return 0


def write_review(onto, profiles, movable, carded, tier, ask_gap, split):
    """판정받을 것만 담은 검토표. draft_review.xlsx 와 같은 방식."""
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "axis_review"
    ws.append(["축", "온톨로지ID", "도메인", "움직이는 제형",
               "카드 있는 제형", "무엇을 묻나", "판정", "메모"])
    P = len(profiles)
    seen = set()
    for n, t, ps in split:
        seen.add(t)
        ws.append([onto.label(t), t, t.split(".")[1],
                   f"{n}/{P}: {', '.join(ps)}",
                   ", ".join(p for p in profiles if t in carded[p]) or "없음",
                   "제형이 함의하는 축인가, 아니면 엣지가 덜 쓰인 것인가?",
                   "", ""])
    for t, ps in sorted(ask_gap.items()):
        if t in seen or len(ps) < P:
            continue
        ws.append([onto.label(t), t, t.split(".")[1],
                   f"{P}/{P}: 전 제형",
                   ", ".join(p for p in profiles if t in carded[p]) or "없음",
                   "전 제형에서 움직이는데 카드가 없다. 보편 축으로 열까?",
                   "", ""])
    ws2 = wb.create_sheet("읽는 법")
    for line in [
        "축 의존성 검토표 — 무엇을 판정해 달라는 것인가",
        "",
        "'판정' 칸에 아래 중 하나를 적어 주세요.",
        "",
        "  보편      제형과 무관하게 존재한다. 전 제형에 열어야 한다",
        "  제형의존  이 상(相)이 없으면 존재할 수 없다. 메모에 무엇이 필요한지 적어 주세요",
        "            (예: 얼음 / 유상 / 분산 고상 / 자립 그물)",
        "  제품의존  제형이 아니라 제품이 정한다. 제품 사전이 다룰 몫이다",
        "  엣지결손  존재는 하는데 아무도 엣지를 안 썼다. 온톨로지를 채워야 한다",
        "  보류      판단 보류. 이유를 메모에",
        "",
        "왜 묻는가: 지금은 '카드가 있느냐' 로 축의 존재를 판정하고 있습니다.",
        "카드는 누가 썼느냐의 기록이라 물리가 아닙니다. 아이스크림에 짠맛 카드가",
        "없어서, 엔진이 소금은 짜다는 것을 알면서도 물어보지 못했습니다.",
        "",
        "판정이 모이면 렉시콘에 requires 를 붙이고, 그때부터는",
        "'이 제형이 그 상을 제공하는가' 로 계산됩니다.",
        "",
        "자세히: docs/축_의존성_검증전략.md",
    ]:
        ws2.append([line])
    ws2.column_dimensions["A"].width = 78
    for col, w in zip("ABCDEFGH", (18, 32, 8, 46, 30, 44, 12, 30)):
        ws.column_dimensions[col].width = w
    wb.save(OUT_XLSX)
    print(f"\n검토표: {OUT_XLSX}  ({ws.max_row-1}행)")


if __name__ == "__main__":
    sys.exit(main(want_xlsx="--xlsx" in sys.argv))
