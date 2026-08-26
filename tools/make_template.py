# -*- coding: utf-8 -*-
"""
랩에 넘길 빈 데이터 템플릿 생성 (앱 없이 CLI 로).

웜루프는 xlsx 한 개를 먹는다. 컬럼 이름이 곧 규약이라 손으로 만들면 어긋나기
쉽다 — 관능 컬럼이 M 카드의 legacy_column 과 한 글자라도 다르면 그 축은
데이터가 없는 것으로 처리된다. 그래서 여기서 생성한다.

만들어지는 시트
  recipes       sample_id · is_benchmark · notes · ing_*   (배합)
  sensory       sample_id · rep · sens_*                   (벤치마크 상대 -3..+3)
  dictionary    ing_* -> ING.*                             (자동 채움)
  README        축 정의와 평가 요령 (M 카드의 evaluation_note 를 실어 준다)

실행:
    python tools/make_template.py                          # 프로파일 목록
    python tools/make_template.py icecream                 # 팔레트 표의 권장+필수로
    python tools/make_template.py icecream --grade 권장,옵션
    python tools/make_template.py icecream --samples IC01,IC02,IC03
    python tools/make_template.py beverage_rice_milk -o data/beverage_batch2.xlsx
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "app"))
sys.path.insert(0, os.path.join(_ROOT, "engine"))

import dataio      # noqa: E402
import palette     # noqa: E402
from formulator.v2adapter import V2Ontology   # noqa: E402


def main(argv):
    onto = V2Ontology()
    if not argv or argv[0].startswith("-"):
        print("프로파일:")
        for p in sorted(onto.profiles):
            try:
                t = palette.load(p)
                n = len(t.palette(include_restricted=False))
                s = f"팔레트 {n}종"
            except Exception:                                  # noqa: BLE001
                s = "팔레트 표 없음"
            print(f"   {p:24s} {s}")
        print("\n사용: python tools/make_template.py <프로파일> [--grade 권장,옵션] [-o 경로]")
        return 0

    prof = argv[0]
    if prof not in onto.profiles:
        print(f"모르는 프로파일: {prof}\n가능: {sorted(onto.profiles)}")
        return 1

    grades = ("필수", "권장")
    out = os.path.join(_ROOT, "data", f"{prof}_template.xlsx")
    samples = None
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--grade":
            i += 1
            grades = tuple(x.strip() for x in argv[i].split(","))
        elif a in ("-o", "--out"):
            i += 1
            out = argv[i] if os.path.isabs(argv[i]) else os.path.join(_ROOT, argv[i])
        elif a == "--samples":
            i += 1
            samples = [x.strip() for x in argv[i].split(",") if x.strip()]
        else:
            print(f"모르는 인자: {a}")
            return 1
        i += 1

    try:
        t = palette.load(prof)
    except FileNotFoundError as e:
        print(f"{e}\n먼저 `python tools/build_palette.py` 를 돌리세요.")
        return 1

    pal = [r["온톨로지ID"] for r in t.rows if r["등급"] in grades]
    if not pal:
        print(f"등급 {grades} 에 해당하는 재료가 없습니다. 표의 등급을 확인하세요.")
        return 1
    filler = onto.filler_of(prof)
    if filler not in pal:
        pal.append(filler)

    # 범위가 비어 있으면 배합을 못 짜니 알려 준다
    b = t.bounds()
    norange = [g for g in pal if g not in b and g != filler]
    if norange:
        print(f"주의 · 작업 범위가 없는 재료 {len(norange)}종: "
              f"{[g.replace('ING.', '') for g in norange[:8]]}")
        print("      배합을 짤 때 참고할 상·하한이 없습니다. 팔레트 표를 채우는 편이 좋습니다.")

    os.makedirs(os.path.dirname(out), exist_ok=True)
    dataio.write_template(out, onto, prof, pal, sample_ids=samples)

    cards = onto._ref.load_cards(prof, onto.layers)
    print(f"작성: {out}")
    print(f"  프로파일 {prof} · 재료 {len(pal)}종(등급 {'/'.join(grades)}) · 관능 축 {len(cards)}개")
    if samples:
        print(f"  샘플 행 {len(samples)}개를 미리 넣었습니다: {', '.join(samples)}")
    print()
    print("  랩에 넘기기 전에 recipes 시트의 배합을 채우세요.")
    print("  평가가 끝나면 이 파일을 data/ 에 두고 앱에서 고르거나,")
    print("  python -c \"import dataio\" 경로로 바로 학습에 넣을 수 있습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
