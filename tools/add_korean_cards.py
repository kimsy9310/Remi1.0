# -*- coding: utf-8 -*-
"""
M 카드에 한글 필드를 넣는다.

무엇을 어디에 두는가
--------------------
축 이름("단맛")은 카드가 아니라 **Layer L 의 ko 필드**에 있다. 216개 항목
전부 이미 채워져 있다. 같은 축이 프로파일 6곳에 카드로 나타나므로, 이름을
카드에 복사하면 사본 6개가 따로 놀게 된다. 이름을 고칠 곳은 렉시콘 한 군데다.

카드에 넣는 것은 **카드 고유의 것** — 같은 축이라도 맥락에 따라 달라지는 말:

    ko.anchors         -3 / 0 / +3 이 무슨 뜻인지. 평가자에게 그대로 읽힌다.
    ko.jar_target      JAR 카드의 목표를 한글로.
    ko.evaluation_note 평가할 때의 주의.
    ko.pitfalls        이 축에서 자주 빠지는 함정.

카드의 note 는 온톨로지를 고치는 사람에게 남긴 이력이라 번역하지 않는다.
사용자 화면에 나가지 않는다.

왜 앵커를 전부 채우나
---------------------
70장 중 anchors 가 있는 카드는 10장뿐이었다. 그중 4장은 -3/0/+3 이 아니라
강도 기준점(intensity/reference) 목록이라 뜻이 아예 다르다. 나머지 60장은
비어 있어서 사용자 화면 ② 단계에 아무 설명도 뜨지 않았다. scale_type 이
jar_5 든 diff_7 든 화면은 "기준보다 더/덜" 로 묻기 때문에, 차이 기준의 앵커는
모든 카드에 필요하다.

YAML 을 다시 쓰지 않고 텍스트로 끼워 넣는다. 이 파일들에는 앵커(&id001)와
주석이 있어서 safe_load -> safe_dump 를 거치면 둘 다 사라진다.

    python tools/add_korean_cards.py           # 넣기
    python tools/add_korean_cards.py --check   # 빠진 것만 보고
"""
from __future__ import annotations

import glob
import io
import os
import sys

import yaml

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAYERS = os.path.join(HERE, "ontology_v2", "layers")

SAME = "기준과 구분되지 않는다"

# ---------------------------------------------------------------- 앵커
# 축마다 -3 / +3. 0 은 전부 SAME 이다. 결함 축도 화면이 차이 척도로 묻기
# 때문에 "없다/있다" 가 아니라 "기준보다 덜하다/더하다" 로 쓴다.
ANCHORS = {
    # --- 맛
    "L.ta.sweet": ("기준보다 뚜렷하게 덜 달다", "기준보다 뚜렷하게 더 달다"),
    "L.ta.sour": ("기준보다 뚜렷하게 덜 시다", "기준보다 뚜렷하게 더 시다"),
    "L.ta.salty": ("기준보다 뚜렷하게 덜 짜다", "기준보다 뚜렷하게 더 짜다"),
    "L.ta.umami": ("감칠맛이 기준보다 뚜렷하게 약하다", "감칠맛이 기준보다 뚜렷하게 강하다"),
    "L.ta.bitter": ("쓴맛이 기준보다 뚜렷하게 약하다", "쓴맛이 기준보다 뚜렷하게 강하다"),
    "L.ta.aftertaste_length": ("뒷맛이 기준보다 뚜렷하게 빨리 사라진다",
                              "뒷맛이 기준보다 뚜렷하게 오래 남는다"),
    # --- 식감
    "L.tx.body": ("기준보다 뚜렷하게 묽고 물 같다", "기준보다 뚜렷하게 묵직하고 꽉 찬다"),
    "L.tx.creaminess": ("기준보다 뚜렷하게 덜 크리미하다", "기준보다 뚜렷하게 더 크리미하다"),
    "L.tx.thickness": ("기준보다 뚜렷하게 덜 걸쭉하다", "기준보다 뚜렷하게 더 걸쭉하다"),
    "L.tx.hardness": ("기준보다 뚜렷하게 무르다 (뜨기 쉽다)",
                      "기준보다 뚜렷하게 단단하다 (뜨기 힘들다)"),
    "L.tx.icy": ("얼음 씹힘이 기준보다 뚜렷하게 적다 (더 매끄럽다)",
                 "얼음 씹힘이 기준보다 뚜렷하게 많다 (서걱거린다)"),
    "L.tx.smoothness": ("기준보다 뚜렷하게 덜 매끄럽다", "기준보다 뚜렷하게 더 매끄럽다"),
    "L.tx.gumminess": ("기준보다 뚜렷하게 덜 뭉친다", "기준보다 뚜렷하게 검처럼 뭉친다"),
    "L.tx.cold_perceived": ("기준보다 뚜렷하게 덜 차갑게 느껴진다",
                            "기준보다 뚜렷하게 더 차갑게 느껴진다"),
    "L.tx.melting": ("기준보다 뚜렷하게 천천히 녹는다", "기준보다 뚜렷하게 빨리 녹는다"),
    "L.tx.oiliness": ("기름진 느낌이 기준보다 뚜렷하게 적다",
                      "기름진 느낌이 기준보다 뚜렷하게 많다"),
    "L.tx.cling": ("기준보다 뚜렷하게 덜 붙고 흘러내린다",
                   "기준보다 뚜렷하게 잘 붙어 코팅된다"),
    "L.tx.spreadability": ("기준보다 뚜렷하게 펴 바르기 어렵다",
                           "기준보다 뚜렷하게 잘 펴진다"),
    "L.tx.mouthcoating_persistence": ("코팅감이 기준보다 뚜렷하게 빨리 사라진다",
                                      "코팅감이 기준보다 뚜렷하게 오래 남는다"),
    "L.tx.pourability": ("기준보다 뚜렷하게 잘 따라지지 않는다",
                         "기준보다 뚜렷하게 잘 따라진다"),
    "L.tx.grittiness": ("꺼끌거림이 기준보다 뚜렷하게 적다",
                        "꺼끌거림이 기준보다 뚜렷하게 많다"),
    "L.tx.perceived_piece_size": ("건더기가 기준보다 뚜렷하게 잘다",
                                  "건더기가 기준보다 뚜렷하게 굵다"),
    # --- 외관
    "L.ap.cloudy": ("기준보다 뚜렷하게 맑다", "기준보다 뚜렷하게 뿌옇다"),
    "L.ap.color_intensity": ("색이 기준보다 뚜렷하게 옅다", "색이 기준보다 뚜렷하게 진하다"),
    "L.ap.glossy": ("윤기가 기준보다 뚜렷하게 덜하다", "윤기가 기준보다 뚜렷하게 더하다"),
    "L.ap.milky_whiteness": ("흰빛이 기준보다 뚜렷하게 약하다",
                             "기준보다 뚜렷하게 뽀얗게 희다"),
    "L.ap.oil_ring": ("기준보다 확실히 깨끗하다 (고리가 보이지 않는다)",
                      "기준보다 뚜렷한 기름 고리가 목이나 표면에 보인다"),
    "L.ap.separated": ("기준보다 확실히 안정적이다 (분리 흔적 없음)",
                       "기준보다 층이 뚜렷하게 갈라졌다"),
    "L.ap.serum_layer": ("기준보다 웃물이 확실히 적다", "기준보다 웃물이 뚜렷하게 많이 고였다"),
    "L.ap.sediment": ("기준보다 침전이 확실히 적다", "기준보다 침전이 뚜렷하게 많고 굳었다"),
    "L.ap.darkened": ("기준보다 뚜렷하게 밝다", "기준보다 뚜렷하게 어두워졌다"),
    # --- 향
    "L.ar.rancid_oxidized": ("기준보다 뚜렷하게 깨끗하다",
                             "쩐내·종이·절은 기름 냄새가 기준보다 뚜렷하다"),
    "L.ar.coffee": ("커피 향이 기준보다 뚜렷하게 약하다", "커피 향이 기준보다 뚜렷하게 강하다"),
    "L.ar.milky": ("우유 향이 기준보다 뚜렷하게 약하다", "우유 향이 기준보다 뚜렷하게 강하다"),
    "L.ar.cooked_rice": ("밥 향이 기준보다 뚜렷하게 약하다", "밥 향이 기준보다 뚜렷하게 강하다"),
    "L.ar.dried_red_chili": ("건고추 향이 기준보다 뚜렷하게 약하다",
                             "건고추 향이 기준보다 뚜렷하게 강하다"),
    "L.ar.soy_fermented_jang": ("장 향이 기준보다 뚜렷하게 약하다",
                                "장 향이 기준보다 뚜렷하게 강하다"),
    # --- 화학감각
    "L.ch.pungent_hot": ("기준보다 뚜렷하게 덜 맵다", "기준보다 뚜렷하게 더 맵다"),
    "L.ch.heat_linger": ("매운 기운이 기준보다 뚜렷하게 빨리 가신다",
                         "매운 기운이 기준보다 뚜렷하게 오래 간다"),
}

# ---------------------------------------------------------------- JAR 목표
JAR = {
    "match benchmark": "기준과 같게",
    "match or exceed benchmark": "기준과 같거나 그 이상",
    "none detectable": "느껴지지 않을 것",
    "no visible ring": "눈에 보이는 기름 고리가 없을 것",
    "not gummy": "검처럼 뭉치지 않을 것",
    "not greasy": "기름지지 않을 것",
    "as smooth as benchmark or smoother": "기준만큼 매끄럽거나 더 매끄럽게",
    "as smooth as the benchmark": "기준만큼 매끄럽게",
    "as bitter as the benchmark": "기준만큼의 쓴맛",
    "as hot as the benchmark": "기준만큼의 매운맛",
    "lingers like the benchmark": "여운이 기준만큼 남을 것",
    "coats like benchmark": "기준만큼 코팅될 것",
}

# ------------------------------------------------- 평가 주의 (프로파일, 축)
EVAL = {
    ("beverage", "L.ta.sweet"):
        "마시는 온도에서 평가하세요. 차가우면 단맛이 눌립니다(R-2 저온→단맛).",
    ("beverage", "L.ap.oil_ring"):
        "따로 보관해 둔 병으로 하는 저장 후 합·부 판정입니다(스펙 5.8).",

    ("beverage_coffee_milk", "L.ta.sweet"):
        "마시는 온도에서 평가하세요. 차가우면 단맛이 눌립니다(R-2 저온→단맛).",
    ("beverage_coffee_milk", "L.ap.oil_ring"):
        "따로 보관해 둔 병으로 하는 저장 후 합·부 판정입니다(스펙 5.8).",
    ("beverage_coffee_milk", "L.ta.bitter"):
        "제품 단위로 켠 축입니다. 기본 음료 프로파일에서 쓴맛은 결함 감시 축이지만 "
        "커피우유에서는 제품 성격을 정하는 축입니다. 사람마다 감지 역치가 크게 달라 "
        "반복 시료를 쓰세요.",

    ("beverage_rice_milk", "L.ta.sweet"):
        "마시는 온도에서 평가하세요. 차가우면 단맛이 눌리므로(R-2 저온→단맛), "
        "기준보다 차게 마신 시료는 배합 때문이 아닌 이유로 낮게 나옵니다.",
    ("beverage_rice_milk", "L.ar.cooked_rice"):
        "이 제품의 정체성 축이지 결함 축이 아닙니다 — 높일수록 좋은 것이 아니라 "
        "맞춰야 할 목표입니다. 코 뒤로 올라오는 향이므로 삼킨 뒤에 판단하고, "
        "잔 위의 냄새로 판단하지 마세요.",
    ("beverage_rice_milk", "L.tx.oiliness"):
        "산패취(L.ar.rancid_oxidized)와 분리해 둔 '신선한 기름' 쪽 읽기입니다. "
        "이 축의 정의대로 향이 아니라 입천장에 남는 코팅을 기준으로 매기세요.",
    # 평가자에게 읽히는 글이다. 온톨로지 이력(review_items·스펙 절 번호)은
    # 영문 evaluation_note 에 그대로 남아 있으므로 여기 옮기지 않는다.
    ("beverage_rice_milk", "L.ar.rancid_oxidized"):
        "갓 만든 시료에서 매기는 점수입니다. 훈련되지 않은 평가자는 산패취를 늦게, "
        "들쭉날쭉하게 감지하므로 작은 차이는 잡음으로 보세요. 이 축으로 결정을 "
        "내릴 때는 어느 시료인지 모르게 하고 두 번 이상 맡아 보셔야 합니다.",
    ("beverage_rice_milk", "L.tx.body"):
        "입에 넣었을 때의 묵직함과 꽉 찬 느낌을 봅니다. 크리미함(매끄럽고 지방 같은 "
        "질감)과 헷갈리기 쉬우니 바디감을 먼저 판단하세요.",
    ("beverage_rice_milk", "L.tx.creaminess"):
        "바디감과 다릅니다 — 바디감은 묵직함이고 크리미함은 매끄럽고 지방 같은 "
        "질감입니다. 패널이 둘을 섞어 답하므로 바디감을 먼저, 크리미함을 나중에 묻는 "
        "순서를 지키세요.",

    ("icecream", "L.ta.sweet"):
        "저온 억제가 강합니다. 먹는 온도에서 평가하고, 상온에서 녹은 상태로는 절대 "
        "평가하지 마세요.",
    ("icecream", "L.tx.hardness"):
        "먹는 온도에서 판단하세요('기준보다 뜨기 힘든가?'). 당을 줄이면 얼음 비율이 "
        "올라가 더 단단해집니다.",
    ("icecream", "L.tx.gumminess"):
        "결함 감시: 안정제 과다(하이드로콜로이드 과량).",

    ("sauce_ow", "L.tx.oiliness"):
        "결함 감시: 표면의 자유 기름막은 유화가 깨졌다는 신호입니다. 바람직한 "
        "크리미함과는 다른 축입니다.",
    ("sauce_ow", "L.tx.mouthcoating_persistence"):
        "삼킨 뒤의 시간 축이라 편차가 큽니다. core 로 올린다면 반복 시료가 필요합니다.",
    ("sauce_ow", "L.ta.bitter"):
        "결함 감시. 떫음과 헷갈리지 않았는지 먼저 확인하세요.",
    ("sauce_ow", "L.ap.separated"):
        "따로 둔 병으로 하는 저장 후 합·부 판정입니다(스펙 5.8): 눈에 보이는 크리밍·"
        "웃물·자유 기름.",

    ("suspension", "L.ch.pungent_hot"):
        "매운맛은 시료를 거듭할수록 쌓입니다. 시료 사이에 쉬는 시간을 두고 기준 시료를 "
        "다시 맛보세요.",
    ("suspension", "L.ch.heat_linger"):
        "삼킨 뒤에 물으세요 — '기준보다 매운 기운이 오래 갔나요?' 지방이 있으면 "
        "여운이 길어집니다.",
    ("suspension", "L.ta.bitter"):
        "결함 감시. 쓴맛이 보고되면 떫음(입안이 마르고 조이는 느낌)부터 확인하세요 — "
        "훈련되지 않은 평가자는 둘을 섞습니다. 떫음 자체는 카드가 없습니다"
        "(물어보기 어려움 판정).",
    ("suspension", "L.ta.aftertaste_length"):
        "시간 축이라 편차가 가장 큽니다. core 로 올린다면 반복을 늘리세요.",
    ("suspension", "L.ap.serum_layer"):
        "따로 둔 병으로 3일 합·부 판정(스펙 5.8). 스토크스 규칙: 3일에 웃물이 없으면 "
        "28일에도 대체로 없습니다.",
    ("suspension", "L.ap.sediment"):
        "3일 합·부 판정. 중요한 것은 다시 섞이는지입니다 — 흔들어 풀리면 합격, "
        "단단히 굳은 덩어리면 불합격.",
}

# ------------------------------------------------------- 함정 (프로파일, 축)
PITFALLS = {
    ("beverage_rice_milk", "L.ar.cooked_rice"): [
        "단맛이 올라가면 밥 향이 더 강하게 느껴집니다. 두 축은 따로 나눠서 평가하세요."],
    ("beverage_rice_milk", "L.tx.oiliness"): [
        "유화가 깨지면 자유 기름 때문에 기름짐이 높게 나옵니다 — 넣은 양 때문이 아니라 "
        "물리적인 이유입니다. 크리밍·분리를 함께 기록해 둬야 둘을 구분할 수 있습니다."],
    ("beverage_rice_milk", "L.ar.rancid_oxidized"): [
        "해바라기유는 산화가 잘 됩니다. 기름 종류를 바꾸면 이 축이 넣은 양과 뒤섞입니다."],
    ("beverage_rice_milk", "L.tx.creaminess"): [
        "검(gum)으로 만든 걸쭉함은 바디감으로는 읽히지만 크리미함으로는 읽히지 "
        "않습니다. 두 축이 같이 움직이면 패널이 한 질문에 두 번 답하고 있을 "
        "가능성이 큽니다."],
}


def _q(s):
    """YAML 스칼라로 안전하게. 한 줄 작은따옴표 스타일."""
    return "'" + str(s).replace("'", "''") + "'"


def block(profile, term, card, indent="  "):
    """카드 하나에 끼워 넣을 ko 블록."""
    lo, hi = ANCHORS[term]
    L = [f"{indent}ko:"]
    L.append(f"{indent}  anchors:")
    L.append(f"{indent}    '-3': {_q(lo)}")
    L.append(f"{indent}    '0': {_q(SAME)}")
    L.append(f"{indent}    '+3': {_q(hi)}")
    jt = card.get("jar_target")
    if jt:
        L.append(f"{indent}  jar_target: {_q(JAR[jt])}")
    ev = EVAL.get((profile, term))
    if ev:
        L.append(f"{indent}  evaluation_note: {_q(ev)}")
    pf = PITFALLS.get((profile, term))
    if pf:
        L.append(f"{indent}  pitfalls:")
        for p in pf:
            L.append(f"{indent}  - {_q(p)}")
    return "\n".join(L) + "\n"


def main(check=False):
    files = sorted(glob.glob(os.path.join(LAYERS, "layerM_cards_*.yaml")))
    total = added = 0
    problems = []

    for path in files:
        prof = os.path.basename(path)[len("layerM_cards_"):-len(".yaml")]
        doc = yaml.safe_load(io.open(path, encoding="utf-8"))
        cards = {c["term_id"]: c for c in doc["measurement_cards"]}
        total += len(cards)

        for t, c in cards.items():
            if t not in ANCHORS:
                problems.append(f"{prof}: {t} 앵커 표에 없음")
            jt = c.get("jar_target")
            if jt and jt not in JAR:
                problems.append(f"{prof}: {t} jar_target 미번역 {jt!r}")
            if c.get("evaluation_note") and (prof, t) not in EVAL:
                problems.append(f"{prof}: {t} evaluation_note 미번역")
            if c.get("pitfalls") and (prof, t) not in PITFALLS:
                problems.append(f"{prof}: {t} pitfalls 미번역")
        # 표에만 있고 카드에 없는 번역 (오타로 영영 안 쓰이는 것)
        for (p, t) in list(EVAL) + list(PITFALLS):
            if p == prof and t not in cards:
                problems.append(f"{prof}: {t} 번역만 있고 카드가 없음")

        if check:
            continue

        lines = io.open(path, encoding="utf-8").read().splitlines(True)
        out = []
        for ln in lines:
            out.append(ln)
            s = ln.rstrip("\n")
            if not s.startswith("- term_id: "):
                continue
            t = s[len("- term_id: "):].strip()
            if cards[t].get("ko"):          # 이미 있으면 건드리지 않는다
                continue
            out.append(block(prof, t, cards[t]))
            added += 1
        io.open(path, "w", encoding="utf-8", newline="\n").write("".join(out))

    if problems:
        print("점검에서 걸린 것:")
        for p in problems:
            print("  -", p)
    else:
        print(f"점검 통과 — 카드 {total}장 모두 번역 대상이 준비됨")
    if not check:
        print(f"ko 블록 {added}장에 삽입 (이미 있던 카드는 건너뜀)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(check="--check" in sys.argv))
