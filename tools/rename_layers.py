# -*- coding: utf-8 -*-
"""
레이어 이름을 글자에서 낱말로 (2026-09-10).

왜
--
일곱 층 가운데 넷은 이미 글자가 뜻이었다 - L(exicon) · R(elation) ·
S(tructure) · M(easurement). 나머지 셋이 문제였다.

    A   담긴 ID 는 P.* 인데 글자는 A. 글자와 내용이 안 맞는다
    C   무엇의 약자인지 아무 데도 없다. 담긴 것은 ING.* · FT.*
    O   아직 만들지도 않은 층인데 글자가 먼저 박혔다

그래서 A 가 특히 헷갈렸다. 온톨로지 지도를 만들며 Layer A 를 "재료와 관능
사이의 배선" 이라고 잘못 적었는데, 사실은 물성의 이름·단위·측정법만 담은
사전이다. 파일을 열지 않으면 글자 A 로는 알 길이 없다.

범위 (사용자 결정 2026-09-10)
----------------------------
    바꾼다      문서 · 주석 · 검사 출력 - 사람이 읽는 모든 곳
    안 바꾼다   파일명 (layerA_parameters.yaml)
    안 바꾼다   ID 접두어 (P.* · L.* · ING.*)
    안 바꾼다   YAML meta 의 `layer: A` - 그건 산문이 아니라 데이터다

파일명이 글자를 그대로 들고 있으므로 낱말과 파일을 잇는 다리가 필요하다.
CLAUDE.md 의 용어집이 그 다리다.

Layer B 는 왜 남기나
--------------------
v1 이 지금의 LEXICON 을 Layer B 라고 불렀다. 16군데 남아 있는데 성격이 둘로
갈린다.

    현재 구조를 설명하는 것 (12건)   고친다 - 죽은 이름으로 산 구조를 말한다
    v1.1 감사 이력 (4건, 렉시콘)     남긴다 - 그때 실제로 그렇게 불렸다

이력을 고치면 기록이 아니라 개작이 된다(불변식 3의 정신). 용어집이 설명한다.

    python tools/rename_layers.py            # 무엇이 바뀌는지만 본다
    python tools/rename_layers.py --write    # 실제로 바꾼다
"""
from __future__ import annotations

import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NAMES = {
    "L": "LEXICON",
    "A": "PARAMETER",
    "C": "INGREDIENT",       # 2026-09-10 EFFECT -> 2026-09-11 INGREDIENT
    "R": "RELATION",
    "S": "STRUCTURE",
    "M": "AXIS_CARD",        # MEASUREMENT -> PRODUCT_CARD -> AXIS_CARD (09-11 두 층)
    "O": "PROCESS",
}

# v1 이름. 현재 구조를 설명하는 자리에서만 고친다.
DEAD = {"B": "LEXICON"}

# 2단계 (2026-09-11): 낱말 -> 낱말. 첫 개명이 틀린 이름을 둘 박았다.
#   MEASUREMENT  "실험 데이터 같다" (사용자). 카드에 실측값은 한 줄도 없다 -
#                한 축을 이 맥락에서 어떻게 읽고 점수 매길지의 정의다.
#                제품의 성질을 기록하는 카드라 PRODUCT_CARD.
#   EFFECT       "이름이 왜 EFFECT 인지" (사용자). 그 층은 재료 데이터베이스인데
#                이름이 그 안의 엣지를 가리켰다. INGREDIENT.
# 대문자 통째 낱말만 잡는다. `effects:` 같은 YAML 키는 소문자라 안 걸린다.
# 3단계 (2026-09-11 오후): 두 층으로 가르면서 이름이 한 번 더 움직인다.
#   제형 축 카드(layerM_cards_<제형>.yaml, 공유)      -> AXIS_CARD
#   제품 한 장(projects/<제품>/product_card.yaml)      -> 이것이 진짜 PRODUCT_CARD
# 순서가 중요하다 - MEASUREMENT 와 PRODUCT_CARD 가 둘 다 AXIS_CARD 로 가야
# 옛 문서와 새 문서가 같은 자리에 닿는다.
WORDS = {"MEASUREMENT": "AXIS_CARD", "PRODUCT_CARD": "AXIS_CARD",
         "EFFECT": "INGREDIENT"}

# 제품 한 장을 말하는 자리는 PRODUCT_CARD 그대로 둔다.
# CLAUDE.md 는 이름의 이력을 적고 있어 손으로 고친다.
WORDS_SKIP = {"product_card.yaml", "v2adapter.py", "CLAUDE.md"}

# 이 파일의 Layer B 는 전부 v1.1 감사 이력이다. 건드리지 않는다.
DEAD_SKIP = {"layerL_lexicon.yaml"}

# 사용자 말을 그대로 인용한 자리. "Layer S 의 경계를 다시 긋자" 같은 문장은
# 그분이 그렇게 말씀하신 기록이라 낱말로 바꾸면 인용이 아니게 된다.
QUOTE_SKIP = {"layer_boundaries.md", "CLAUDE.md"}

# v1 로더 계열. **글자가 v2 와 다른 층을 가리킨다** -
#
#     v1 Layer A = structure classes    v2 에서는 STRUCTURE
#     v1 Layer B = sensory attributes   v2 에서는 LEXICON
#     v1 Layer C = tags + ingredients   v2 도 같다 (EFFECT)
#
# 기계로 치환하면 조용히 틀린 이름이 박힌다. 손으로 고쳤다.
# (이 사실 자체가 개명의 근거다 - 글자가 세대마다 다른 뜻이었다.)
V1_SKIP = {"ontology.py", "optimize.py", "cypher.py", "filters.py",
           "projection.py"}

EXT = (".yaml", ".py", ".md")
SKIP_DIRS = {".git", "__pycache__", "_deprecated", "migration", ".claude"}
SKIP_FILES = {"rename_layers.py"}


def targets():
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith(EXT) and f not in SKIP_FILES and f not in V1_SKIP:
                yield os.path.join(base, f)


def convert(text, fname):
    """치환하고 (새 텍스트, 건수) 를 낸다."""
    n = 0
    if fname not in QUOTE_SKIP:
        for letter, word in NAMES.items():
            # `Layer A` 만 잡는다. `layerA_parameters.yaml` 은 파일명이라 안 걸린다
            # (앞이 소문자 + 뒤에 밑줄). 단어 경계로 A 뒤에 글자가 오는 것도 막는다.
            pat = re.compile(r"\bLayer " + letter + r"\b")
            text, k = pat.subn(word, text)
            n += k
        if fname not in DEAD_SKIP:
            for letter, word in DEAD.items():
                pat = re.compile(r"\bLayer " + letter + r"\b")
                text, k = pat.subn(word, text)
                n += k
    if fname not in WORDS_SKIP:
        for old_w, new_w in WORDS.items():
            pat = re.compile(r"\b" + old_w + r"\b")
            text, k = pat.subn(new_w, text)
            n += k
    return text, n


def main(write=False):
    total, touched = 0, []
    for path in targets():
        try:
            src = io.open(path, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        out, n = convert(src, os.path.basename(path))
        if not n:
            continue
        total += n
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        touched.append((rel, n))
        if write:
            io.open(path, "w", encoding="utf-8", newline="\n").write(out)

    print("=" * 62)
    print("  레이어 이름: 글자 -> 낱말" + ("" if write else "   (미리보기)"))
    print("=" * 62)
    for word, letter in sorted((v, k) for k, v in NAMES.items()):
        print(f"  Layer {letter}  ->  {word}")
    print(f"  Layer B  ->  LEXICON   (v1 이름. 감사 이력 4건은 그대로 둔다)")
    for a, b in WORDS.items():
        print(f"  {a:<11}  ->  {b}   (2단계 2026-09-11)")
    print()
    for rel, n in sorted(touched, key=lambda x: -x[1]):
        print(f"  {n:>3}건  {rel}")
    print(f"\n  파일 {len(touched)}개 · {total}건")
    if not write:
        print("\n  실제로 바꾸려면: python tools/rename_layers.py --write")
    return 0


if __name__ == "__main__":
    sys.exit(main(write="--write" in sys.argv))
