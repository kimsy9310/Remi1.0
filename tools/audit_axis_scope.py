# -*- coding: utf-8 -*-
"""
축 의존성 감사 — 어떤 축이 어디서 조종 가능한가 (착수 순서 1.8).

판정 규칙은 하나 — 도달 가능성
------------------------------
    축이 이 제형에 존재한다  <=>  이 제형에서 그 축에 닿는 경로가 있다

`effects_for(profile)` 가 이미 그것을 계산한다. C 엣지(스코프 적용)와 R-1 합성
(스코프 적용)을 걸어서 도달 가능한 축을 낸다. **새 필드가 필요 없다.**

처음에는 렉시콘에 `requires: [ice, oil_phase, ...]` 를 붙여 물리적 전제를
선언하려 했다. 접었다.

  1. 한 감각이 한 상(相)에만 의존하지 않는다. 크리미함은 지방·점도·매끄러움이
     얽혀 있고 AND 인지 OR 인지까지 적어야 한다. 216개에 그건 비현실적이고,
     15개만 적으면 나머지 201개를 "전제 없음" 이라 단언하는 셈이다.
  2. **이미 적혀 있다.** 갈리는 축 22개 중 13개가 R-1 을 거쳐야만 닿고, 그
     R-1 에 `scope: SC.frozen.ice_cream` 같은 것이 붙어 있다. `requires` 는
     그 두 번째 사본이 되고, 두 곳에 적으면 갈라진다.
  3. 도달 가능성은 **다중 의존을 공짜로** 처리한다. 경로가 어떤 조합을 거치든
     하나라도 있으면 도달. 나열할 것이 없다.

축이 존재하는 이유는 다섯
-------------------------
    보편        전제 없음. 짠맛 — 먹을 수 있으면 짤 수 있다
    제형의존    제형이 그 상을 줘야 한다. 얼음 씹힘 <- 얼음. 팔레트로 못 고친다
    재료의존    그 재료가 팔레트에 있어야 한다. 커피 향 <- 커피. 팔레트로 켠다
    공정의존    공정이 정한다. 꺼끌거림 <- 얼마나 갈았나. 재료로는 못 켠다
    엣지결손    존재하는데 온톨로지에 엣지가 없다. 고쳐야 할 것

**공정의존은 2026-09-10 에 대장에서 나왔다.** 건더기 크기 판정에 사용자가
적어 주신 칸이고, 재 보니 스펙 5.9 가 "액추에이터 없는 R-1" 이라 플래그를
달아 두던 파라미터 셋(P.particle_size_d90 · P.flavor_release_dynamics ·
P.serving_temperature)을 정확히 설명한다. 재료 엣지가 0건인 것이 당연하다 —
분쇄·향방출·제공온도는 재료가 아니라 공정이 정한다. 결함이 아니라 PROCESS
의 빈 소켓이었고, 이름이 없어서 결함으로 보였다. ⑥ 절이 그 목록이다.

"제품의존" 은 없앴다. 커피 향이 존재하는 것은 "커피우유라는 제품이라서" 가
아니라 "커피를 넣어서" 다 — 재료의존이다. 제품이 정하는 것은 존재 여부가 아니라
존재하는 축 가운데 무엇을 앞세울지(정체성 축 2~3개)이고, 그건 다른 층이다.

그러면 이 도구가 하는 일
------------------------
도달 가능성이 못 하는 것이 하나 있다 — 어떤 축이 안 잡힐 때 **물리적으로
불가능해서인지 엣지를 안 써서인지** 가리지 못한다. 그건 계산이 아니라 판단이다.

그래서 판단이 필요한 자리만 골라 낸다. 특히 ③ **같은 제형 부류인데 도달이
갈리는 축** — 같은 `structure_class` 끼리는 물리가 같으므로, 한쪽에서만
도달하면 거의 확실히 엣지 결손이다. 이것이 핵심 산출물이다.

주의: `effects_for` 는 재료 118종 **전부**를 훑는다. 바닐라 향이 "전 제형에서
움직인다" 고 나오는 것은 바닐라 추출물을 넣기만 하면 어디서든 난다는 뜻이지
제형 무관이라는 뜻이 아니다 — 재료의존이다.

    python tools/audit_axis_scope.py            # 보고서
    python tools/audit_axis_scope.py --xlsx     # 판정 대장 (data/axis_review.xlsx)

자세한 배경: docs/축_의존성_검증전략.md
"""
from __future__ import annotations

import collections
import os
import sys

# 파이프·리다이렉트로 나갈 때 윈도우 파이썬은 cp949 를 쓴다. 이 보고서는
# em dash(—)를 쓰므로 거기서 죽었다. 검사가 반만 돌고 멈추는 것을 막는다.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(HERE, "engine")]

from formulator.v2adapter import V2Ontology            # noqa: E402

OUT_XLSX = os.path.join(HERE, "data", "axis_review.xlsx")

# 대장에 적을 수 있는 판정. 한 칸에 여럿 적어도 된다("엣지결손, 제형의존").
VERDICTS = ("보편", "제형의존", "재료의존", "공정의존", "엣지결손", "보류")


def read_ledger(path=OUT_XLSX):
    """
    판정 대장을 읽는다. 없으면 빈 dict.

    이 도구는 오래 **쓰기만** 했다. 그래서 사람이 한 번 판정한 항목이 돌릴
    때마다 다시 "고쳐야 할 목록" 에 떠서, 기각한 것과 아직 안 본 것이 섞였다.
    판정은 물리에 대한 것이라 배선이 바뀌어도 유효하다 — 읽어서 갈라 놓는다.
    """
    if not os.path.exists(path):
        return {}
    try:
        import openpyxl
    except ImportError:
        return {}
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    if "판정대장" not in wb.sheetnames:
        return {}
    out = {}
    for row in wb["판정대장"].iter_rows(min_row=2, values_only=True):
        if not row or not row[1]:
            continue
        verdict = (row[6] or "").strip() if len(row) > 6 else ""
        memo = (row[7] or "").strip() if len(row) > 7 else ""
        if not verdict:
            continue
        tags = {v for v in VERDICTS if v in verdict}
        out[row[1]] = dict(raw=verdict, tags=tags, memo=memo)
    return out


def process_gated(onto):
    """
    R-1 이 쓰는데 재료·태그 엣지가 하나도 없는 파라미터. 스펙 5.9 가 플래그를
    달던 자리이고, 대장이 준 이름은 **공정의존** 이다.

    반환: [(파라미터, [그 파라미터가 무는 축들])]
    """
    moved = set()
    for src in (onto.tags, onto.ingredients):
        for d in src.values():
            for e in (d.get("effects") or d.get("overrides") or []):
                to = e.get("to") or ""
                if to.startswith("P."):
                    moved.add(to)
    gates = collections.defaultdict(set)
    for r in onto.stack["R"].get("relations_proxy", []) or []:
        gates[r.get("parameter")].add(r.get("percept"))
    return [(pa, sorted(ts)) for pa, ts in sorted(gates.items())
            if pa and pa not in moved]

# 도메인별 예상. 감사가 이것을 뒤집으면 그 자체가 발견이다.
DOMAIN = {
    "ta": ("맛", "보편 — 수용체 수준"),
    "ch": ("화학감각", "보편으로 예상 — 작열은 매트릭스와 무관"),
    "ar": ("향", "재료의존 — 그 재료를 넣으면 켜진다. 제형과 무관"),
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
    ledger = read_ledger()

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
    print(f"    {_gap:,} 칸 중 향(L.ar)이 {_ar:,} 칸이다. 향은 재료의존이라")
    print(f"    그 재료를 팔레트에 넣으면 켜진다 — 결함이 아니다.")
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

    # ------------------------------------- ③ 엣지 결손 (물리로 설명되지 않는다)
    # 같은 structure_class 를 쓰는 프로파일끼리는 물리가 같다. 그런데 한쪽에서만
    # 도달하면 물리가 아니라 엣지를 안 쓴 것이다. 이 감사의 핵심 산출물.
    print("\n" + "-" * 74)
    print("③ 엣지 결손 — 같은 제형 부류인데 도달이 갈리는 축")
    print("-" * 74)
    print("  같은 structure_class 끼리는 물리가 같다. 한쪽에서만 도달하면")
    print("  물리가 아니라 **엣지를 안 쓴 것**이다 — 다만 판정 대장이 아니라고")
    print("  하면 아니다. 대장에 있는 것은 아래에서 갈라 놓는다.")
    fam = collections.defaultdict(list)
    for p in profiles:
        sc = sorted(x for x in onto.profiles[p]["scopes"] if x != "any")
        fam[sc[0] if sc else "?"].append(p)
    leaks = []
    for sc, ps in sorted(fam.items()):
        if len(ps) < 2:
            continue
        for t in sorted(set().union(*[movable[q] for q in ps])):
            miss = [q for q in ps if t not in movable[q]]
            if miss:
                have = [q for q in ps if t in movable[q]]
                leaks.append((sc, t, have, miss))
    print()
    open_leaks = [x for x in leaks if x[1] not in ledger]
    done_leaks = [x for x in leaks if x[1] in ledger]
    if not open_leaks:
        print("  아직 판정 안 된 것: 없음")
    for sc, t, have, miss in open_leaks:
        print(f"  [{sc}] {onto.label(t):<18} 있음 {len(have)}/{len(have)+len(miss)}"
              f"  ·  없음 {miss}")
    if done_leaks:
        print(f"\n  판정 끝 {len(done_leaks)}건 — 대장이 이미 답한 것이다")
        for sc, t, have, miss in done_leaks:
            v = ledger[t]
            memo = ("  " + v["memo"][:38]) if v["memo"] else ""
            print(f"     {onto.label(t):<18} {v['raw']:<26}{memo}")
    print(f"\n  총 {len(leaks)}건 (미판정 {len(open_leaks)} · 판정 끝 {len(done_leaks)})")

    # ------------------------------------- ④ 갈리는 축 (판정 대장 입력)
    split = []
    for t in lex:
        ps = [p for p in profiles if t in movable[p]]
        if 0 < len(ps) < P:
            split.append((len(ps), t, ps))
    split.sort(reverse=True)
    print("\n" + "-" * 74)
    print(f"④ 제형마다 도달이 갈리는 축 {len(split)}개 — 판정 대장 입력")
    print("-" * 74)
    print("  물리(제형의존)인지 누락(엣지결손)인지 계산으로는 못 가른다.")
    print("  대장에서 한 번 정하고, 그 뒤로는 selfcheck 가 지킨다.")
    print()
    todo = 0
    for n, t, ps in split:
        if t.split(".")[1] == "ar" and n < 3:
            continue                      # 향은 재료의존. 여기서 볼 것이 아니다
        short = [p.replace("beverage_", "b_").replace("suspension_", "s_") for p in ps]
        v = ledger.get(t)
        if v:
            mark = v["raw"]
        else:
            mark = "· 미판정 ·"
            todo += 1
        print(f"     {onto.label(t):<18} {n}/{P}  {mark:<28} {short}")
    print(f"\n  미판정 {todo}건 · 판정 끝 {len(ledger)}건")

    # ---------------------------------------------- ④ 전 제형에서 못 움직임
    never = [t for t in lex if not any(t in movable[p] for p in profiles)]
    print("\n" + "-" * 74)
    print(f"⑤ 어느 제형에서도 못 움직이는 축 {len(never)}개")
    print("-" * 74)
    print("  선반 재고다. 결함이 아니지만, 카드를 붙이려면 먼저 엣지가 필요하다.")
    dn = collections.Counter(t.split(".")[1] for t in never)
    for d in ("ar", "tx", "ap", "ta", "ch"):
        if dn.get(d):
            print(f"     L.{d} {DOMAIN[d][0]:<8} {dn[d]:>3}개")

    # ------------------------------------------- ⑥ 공정 액추에이터 대기
    gated = process_gated(onto)
    print("\n" + "-" * 74)
    print(f"⑥ 공정 액추에이터를 기다리는 파라미터 {len(gated)}개 — 공정의존")
    print("-" * 74)
    print("  R-1 이 쓰는데 재료·태그 엣지가 0건인 파라미터다. 스펙 5.9 가")
    print("  \"액추에이터 없는 R-1\" 이라 플래그를 달던 자리이고, 결함이 아니다 —")
    print("  분쇄·향방출·제공온도는 재료가 아니라 공정이 정한다. PROCESS 의 몫.")
    print()
    for pa, ts in gated:
        names = ", ".join(onto.label(t) for t in ts)
        print(f"     {pa:<30} -> {names}")
    if not gated:
        print("     없음")

    if want_xlsx:
        write_review(onto, profiles, movable, carded, tier, split, leaks, ledger)
    return 0


def write_review(onto, profiles, movable, carded, tier, split, leaks, ledger=None):
    """
    판정 대장. `requires` 필드를 만드는 대신 이 표 한 장을 채운다.

    **이미 적힌 판정·메모는 보존한다.** 2026-09-10 에 22행이 채워졌고,
    그냥 덮어쓰면 그것이 날아간다. 도달 제형 숫자는 배선이 바뀌면 갱신되어야
    하지만 판정은 물리에 대한 것이라 그대로 살린다.

    런타임 판정은 도달 가능성이 한다(머리말). 이 표는 도달 가능성이 못 하는
    한 가지 — "안 잡히는 것이 물리인가 누락인가" — 를 한 번 정해 기록한다.
    정해지고 나면 selfcheck 가 지킨다.
    """
    import openpyxl
    P = len(profiles)
    wb = openpyxl.Workbook()

    ws = wb.active
    ws.title = "판정대장"
    ws.append(["축", "온톨로지ID", "도메인", "도달하는 제형", "카드 있는 제형",
               "왜 올라왔나", "판정", "메모"])
    leak_of = {}
    for sc, t, have, miss in leaks:
        leak_of.setdefault(t, []).append((sc, miss))

    for n, t, ps in split:
        if t.split(".")[1] == "ar" and n < 3:
            continue                      # 향은 재료의존. 판정할 것이 아니다
        if t in leak_of:
            miss = leak_of[t][0][1]
            why = (f"같은 제형 부류인데 {miss} 에서만 안 잡힌다. "
                   f"물리로는 설명되지 않는다 — 엣지결손일 가능성이 높다")
        else:
            why = "제형마다 도달이 갈린다. 물리인가 누락인가"
        keep = (ledger or {}).get(t) or {}
        ws.append([onto.label(t), t, t.split(".")[1],
                   f"{n}/{P}: {', '.join(ps)}",
                   ", ".join(p for p in profiles if t in carded[p]) or "없음",
                   why, keep.get("raw", ""), keep.get("memo", "")])

    ws2 = wb.create_sheet("읽는 법")
    for line in [
        "축 판정 대장 — 무엇을 정해 달라는 것인가",
        "",
        "'판정' 칸에 아래 넷 중 하나를 적어 주세요.",
        "",
        "  보편        전제가 없다. 어느 제형에서든 존재한다",
        "              예) 짠맛 — 먹을 수 있으면 짤 수 있다",
        "",
        "  제형의존    제형이 그 상(相)을 줘야 존재한다. 팔레트로는 못 고친다",
        "              예) 얼음 씹힘 — 얼음이 없으면 없다",
        "              메모에 무엇이 필요한지 적어 주세요 (얼음 / 유상 / 분산 고상 …)",
        "",
        "  재료의존    그 재료가 팔레트에 있어야 존재한다. 팔레트로 켠다",
        "              예) 커피 향 — 커피를 넣으면 난다. 음료든 아이스크림이든",
        "",
        "  공정의존    공정이 정한다. 재료로는 못 켠다",
        "              예) 꺼끌거림 — 얼마나 갈았느냐가 정한다",
        "              2026-09-10 대장에서 나온 칸. 스펙 5.9 가 결함으로",
        "              플래그를 달던 파라미터 3개가 전부 여기였다",
        "",
        "  엣지결손    존재는 하는데 온톨로지에 엣지가 없다. 우리가 고쳐야 한다",
        "              예) 걸쭉함이 소스에만 있고 음료에 없다 — 음료도 흐른다",
        "",
        "  보류        판단 보류. 이유를 메모에",
        "",
        "─" * 60,
        "",
        "'제품의존' 은 없앴습니다. 헷갈리는 이름이었습니다 —",
        "커피 향이 존재하는 것은 '커피우유라는 제품이라서' 가 아니라",
        "'커피를 넣어서' 입니다. 즉 재료의존입니다.",
        "제품이 정하는 것은 존재 여부가 아니라, 존재하는 축 가운데",
        "무엇을 앞세울지(정체성 축 2~3개)이고 그건 다른 층의 일입니다.",
        "",
        "─" * 60,
        "",
        "왜 묻는가",
        "",
        "지금은 '카드가 있느냐' 로 축의 존재를 판정하고 있었습니다.",
        "카드는 누가 썼느냐의 기록이지 물리가 아닙니다. 아이스크림에 짠맛",
        "카드가 없어서, 엔진은 소금이 짜다는 것을 알면서도 물어보지",
        "못했습니다.",
        "",
        "앞으로 런타임 판정은 '도달 가능성' 이 합니다 — 이 제형에서 그 축에",
        "닿는 경로가 있으면 존재하고, 없으면 없습니다. 새 필드를 만들지",
        "않습니다. 다중 의존도 경로 탐색이 알아서 처리합니다.",
        "",
        "다만 '안 잡히는 것이 물리인가 우리 누락인가' 는 계산으로 못 가릅니다.",
        "그것만 이 표에서 한 번 정하고, 뒤로는 selfcheck 가 지킵니다.",
        "",
        "자세히: docs/축_의존성_검증전략.md",
    ]:
        ws2.append([line])
    ws2.column_dimensions["A"].width = 76

    ws3 = wb.create_sheet("엣지결손")
    ws3.append(["제형 부류", "축", "온톨로지ID", "도달하는 곳", "안 되는 곳", "메모"])
    for sc, t, have, miss in leaks:
        ws3.append([sc, onto.label(t), t, ", ".join(have), ", ".join(miss), ""])
    for col, w in zip("ABCDEF", (22, 18, 30, 40, 40, 30)):
        ws3.column_dimensions[col].width = w

    for col, w in zip("ABCDEFGH", (18, 30, 8, 44, 30, 52, 12, 34)):
        ws.column_dimensions[col].width = w
    wb.save(OUT_XLSX)
    print()
    print(f"판정 대장: {OUT_XLSX}")
    kept = sum(1 for r in ws.iter_rows(min_row=2, values_only=True) if r[6])
    print(f"  판정대장 {ws.max_row-1}행 (판정 {kept}행 보존) · 엣지결손 {ws3.max_row-1}행")


if __name__ == "__main__":
    sys.exit(main(want_xlsx="--xlsx" in sys.argv))
