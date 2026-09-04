# -*- coding: utf-8 -*-
"""
현탁액에서 제품을 떼어낸다 (착수 순서 1.5).

무엇이 문제였나
---------------
`SC.suspension` 의 정의는 "녹지 않는 고체 입자가 연속된 액상에 분산됨" 뿐이다.
무슨 향이 나는지는 함의하지 않는다. 그런데 core 축 10개 중 4개가 향·화학감각이고
meta 에는 이렇게 적혀 있었다:

    profile: Suspension (solid-in-liquid dispersion) - default product: fermented hot sauce

쌀음료·커피우유는 제품 단위 파일(F7)로 분리돼 있는데 현탁액만 제형 파일 안에
제품이 들어앉았다. 그 결과 사용자가 "현탁액" 을 고르면 매운맛·건고추 향·장 발효
향을 묻는다 — 토마토 살사를 만들려는 사람에게도.

Layer S 는 이미 알고 있었다
---------------------------
suspension 의 relevant_attributes 에서 두 향 축이 slot: flavor_user_slot_1/2 를
달고 있다. meta 에도 "flavor_slots: 2 user-selectable at onboarding" 이라고 적혀
있다. **칸의 개수는 제형이 정하고 칸의 내용은 제품이 채운다** 는 것이 원래
설계인데, 기본값이 값처럼 굳어 default_goal: target 으로 박혔다.

어떻게 가르나
-------------
F7 패턴대로 제품 파일은 **자기완결형**이다(커피우유 11장 = 기본 8 + 제품 3).

    layerM_cards_suspension.yaml            15장 · core 6 · target 0
        └ 제형이 함의하는 것 + 어느 식품에나 있는 기본맛만 남는다

    layerM_cards_suspension_hotsauce.yaml   19장 · core 10 · target 3
        └ 위의 15장 + 제품 축 4장. meta.product: 발효 핫소스

정체성 축은 2~3개다(2026-09-02 결정). 발효 핫소스의 셋은
매운맛 · 건고추 향 · 장 발효 향이고, 나머지 둘은 **삭제가 아니라 강등**이다:

    매운맛 여운  target -> maintain   매운맛의 성질이지 별개 정체성이 아니다
    감칠맛       target -> maintain   장에 딸려 온다

강등된 축은 ② 단계 칩에 그대로 남아 조절할 수 있다. 정체성 표식 자격만 잃는다.

YAML 앵커 주의
--------------
`&id001` 정의가 하필 제거 대상인 첫 카드(L.ch.pungent_hot) 안에 있다. 그냥
지우면 나머지 17개 `*id001` 참조가 전부 깨진다. 카드를 지운 뒤 남은 첫 참조를
정의로 승격시킨다.

    python tools/split_suspension_product.py           # 가르기
    python tools/split_suspension_product.py --check   # 결과만 확인
"""
from __future__ import annotations

import io
import os
import sys

import yaml

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAYERS = os.path.join(HERE, "ontology_v2", "layers")

BASE = os.path.join(LAYERS, "layerM_cards_suspension.yaml")
PROD = os.path.join(LAYERS, "layerM_cards_suspension_hotsauce.yaml")
SFILE = os.path.join(LAYERS, "layerS2_profiles.yaml")

# 제형 파일에서 빼고 제품 파일로 보낼 축
MOVE = ["L.ch.pungent_hot", "L.ch.heat_linger",
        "L.ar.dried_red_chili", "L.ar.soy_fermented_jang"]

# 제품 파일 안에서 target 을 유지할 축 = 발효 핫소스의 정체성 3개
IDENTITY = {"L.ch.pungent_hot", "L.ar.dried_red_chili", "L.ar.soy_fermented_jang"}

# 두 파일 모두에서 target -> maintain 으로 내릴 축
DEMOTE = ["L.ta.umami"]

ANCHOR_DEF = "  active_in: &id001\n  - SC.suspension\n"
ANCHOR_REF = "  active_in: *id001\n"


def split_cards(lines):
    """머리말과 카드 블록들로 가른다. 카드는 '- term_id: X' 로 시작한다."""
    head, cards, cur = [], [], None
    for ln in lines:
        if ln.startswith("- term_id: "):
            if cur:
                cards.append(cur)
            cur = [ln]
        elif cur is not None:
            cur.append(ln)
        else:
            head.append(ln)
    if cur:
        cards.append(cur)
    return head, cards


def term_of(card):
    return card[0][len("- term_id: "):].strip()


def set_goal(card, goal):
    return [("  default_goal: %s\n" % goal) if ln.startswith("  default_goal:") else ln
            for ln in card]


def fix_anchor(cards):
    """
    &id001 정의가 사라졌으면 남은 첫 *id001 참조를 정의로 승격한다.
    이걸 안 하면 YAML 이 UndefinedAlias 로 터진다.
    """
    body = "".join("".join(c) for c in cards)
    if "&id001" in body or "*id001" not in body:
        return cards
    out, done = [], False
    for c in cards:
        if not done and ANCHOR_REF in c:
            i = c.index(ANCHOR_REF)
            c = c[:i] + [ANCHOR_DEF] + c[i + 1:]
            done = True
        out.append(c)
    return out


def main(check=False):
    lines = io.open(BASE, encoding="utf-8").read().splitlines(True)
    head, cards = split_cards(lines)
    have = [term_of(c) for c in cards]
    missing = [t for t in MOVE + DEMOTE if t not in have]
    if missing:
        print("카드에 없는 축:", missing)
        return 1

    # ---------------------------------------------------------- 제품 파일
    # 자기완결형이다. 전부 담되 정체성 3개만 target 으로 남긴다.
    prod = []
    for c in cards:
        t = term_of(c)
        if t in DEMOTE or (t in MOVE and t not in IDENTITY):
            c = set_goal(c, "maintain")
        prod.append(c)

    phead = []
    for ln in head:
        if ln.startswith("  profile:"):
            phead.append("  profile: Suspension (solid-in-liquid dispersion)\n")
            phead.append("  product: fermented hot sauce (product-level activation)\n")
            phead.append("  product_ko: 발효 핫소스\n")
            phead.append(
                "  note: 'PRODUCT-LEVEL ACTIVATION FILE (F7), same pattern as"
                " layerM_cards_beverage_coffee_milk.yaml. The four product axes"
                " (pungent_hot, heat_linger, dried_red_chili, soy_fermented_jang)"
                " lived in the suspension PROFILE file until 2026-09-02. A structure"
                " class implies rheology and appearance, not aroma - a tomato salsa"
                " is the same structure and shares none of them. Identity axes are"
                " capped at 3 (pungent_hot, dried_red_chili, soy_fermented_jang);"
                " heat_linger and umami are demoted to maintain, not removed.'\n")
        elif ln.startswith("  flavor_slots:"):
            phead.append("  flavor_slots: 'filled by this product:"
                         " dried_red_chili + soy_fermented_jang'\n")
        else:
            phead.append(ln)

    # ---------------------------------------------------------- 제형 파일
    base = [c for c in cards if term_of(c) not in MOVE]
    base = [set_goal(c, "maintain") if term_of(c) in DEMOTE else c for c in base]
    base = fix_anchor(base)

    bhead = []
    for ln in head:
        if ln.startswith("  profile:"):
            bhead.append("  profile: Suspension (solid-in-liquid dispersion)\n")
            bhead.append(
                "  note: 'STRUCTURE PROFILE. Carries only what the structure implies"
                " (rheology, appearance) plus the basic tastes every food is scored"
                " on. Product-defining aroma and chemesthesis axes live in a"
                " product-level file - see layerM_cards_suspension_hotsauce.yaml."
                " Split 2026-09-02; before that the fermented hot sauce was baked in"
                " here and every suspension user was asked about chilli.'\n")
        elif ln.startswith("  flavor_slots:"):
            bhead.append("  flavor_slots: '2 - declared here, filled by the product'\n")
        else:
            bhead.append(ln)

    if check:
        print(f"제형 파일 {len(base)}장 · 제품 파일 {len(prod)}장 (쓰지 않음)")
        return 0

    io.open(PROD, "w", encoding="utf-8", newline="\n").write(
        "".join(phead) + "".join("".join(c) for c in prod))
    io.open(BASE, "w", encoding="utf-8", newline="\n").write(
        "".join(bhead) + "".join("".join(c) for c in base))

    # counts 갱신
    for path in (BASE, PROD):
        d = yaml.safe_load(io.open(path, encoding="utf-8"))
        cs = d["measurement_cards"]
        cnt = dict(cards=len(cs),
                   core=sum(1 for c in cs if c["tier"] == "core"),
                   monitored=sum(1 for c in cs if c["tier"] == "monitored"),
                   sample_aged=sum(1 for c in cs
                                   if c.get("evidence_required") == "sample_aged"))
        # counts 는 한 줄이 아니라 중첩 블록이다(cards/core/monitored/sample_aged).
        # 머리만 갈면 자식 줄이 붕 떠서 YAML 이 터진다 — 블록째 갈아야 한다.
        out, in_counts = [], False
        for ln in io.open(path, encoding="utf-8").read().splitlines(True):
            if ln.startswith("  counts:"):
                out.append("  counts:\n")
                for k in ("cards", "core", "monitored", "sample_aged"):
                    out.append("    %s: %d\n" % (k, cnt[k]))
                in_counts = True
                continue
            if in_counts:
                if ln.startswith("    "):          # counts 의 자식 줄
                    continue
                in_counts = False
            out.append(ln)
        io.open(path, "w", encoding="utf-8", newline="\n").write("".join(out))
        tg = sum(1 for c in cs
                 if c["tier"] == "core" and c.get("default_goal") == "target")
        print(f"  {os.path.basename(path):<44} {cnt['cards']}장 · "
              f"core {cnt['core']} · 정체성 축 {tg}")
    return 0


if __name__ == "__main__":
    sys.exit(main(check="--check" in sys.argv))
