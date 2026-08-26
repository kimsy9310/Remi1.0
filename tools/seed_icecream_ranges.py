# -*- coding: utf-8 -*-
"""
아이스크림 팔레트 작업 범위 초안 채우기.

왜 초안인가
-----------
온톨로지의 `limitations` 는 자유 서술이라 기계가 못 읽는다(스펙 G5). 실제로
확인해보니 범위 미입력 39종 중 숫자가 적힌 것은 **잔탄검 하나**뿐이었다
("> ~0.5% -> slimy/stringy"). 온톨로지에서 뽑아낼 수가 없다.

그래서 아이스크림 표준 사용량으로 초안을 넣는다. 백지에서 39개를 쓰는 것보다
39개를 검토하는 편이 훨씬 빠르다. **전부 '검토 필요' 로 표시**하며, 확정된
값이 아니다.

값의 성격
---------
완제품 기준 중량 %. 비건·저당 아이스크림을 전제로 잡았다. 판단 기준:
  - 하한은 그 재료를 넣는 의미가 생기는 최소량
  - 상한은 결함이 나타나기 시작하는 지점(검성·쿨링·모래감 등)
  - DoE 규칙 3 대로 필수 기능 재료에는 0 을 두지 않는다

실행:
    python tools/seed_icecream_ranges.py            # 미입력 항목만 채움
    python tools/seed_icecream_ranges.py --force    # 기존 값도 덮어씀
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "app"))
sys.path.insert(0, os.path.join(_ROOT, "engine"))

import palette  # noqa: E402

PROFILE = "icecream"
BASIS = "표준 사용량(초안) — 검토 필요"

# (하한, 상한, 근거 메모)
SEED = {
    # ---- 지방 · 유지 ----------------------------------------------------
    "ING.coconut_oil":                  (6.0, 14.0,  "유지방 대체 주력. 6% 미만이면 크리미가 안 서고, 14% 넘으면 기름진 느낌"),
    "ING.palm_oil":                     (4.0, 12.0,  "범용 식물지방. 코코넛유보다 보조 위치"),
    "ING.rice_bran_oil":                (3.0, 10.0,  "PUFA 산화 관리 필요 — 상한을 낮게"),
    "ING.high_oleic_sunflower_oil":     (4.0, 10.0,  "산화안정 좋은 액상유"),
    "ING.high_fat_powder":              (3.0, 10.0,  "분말지방. 믹스 편의"),
    "ING.vegan_creamer":                (2.0, 8.0,   "지방+유화 겸. 당을 소량 동반"),
    "ING.prima_creamer":                (2.0, 8.0,   "프리마. 당 소량 기여를 저당 회계에 반영할 것"),
    "ING.hydrogenated_palm_kernel_oil": (1.0, 5.0,   "경질지방 — 소량 구조재. 과하면 왁시"),
    # ---- 감미 · 빙점 ----------------------------------------------------
    "ING.erythritol":                   (2.0, 8.0,   "8% 넘으면 쿨링 오프노트가 뚜렷해진다(HANDOFF 경고)"),
    "ING.high_intensity_sweetener":     (0.01, 0.08, "극소량. 여운·쓴맛이 따라온다"),
    # ---- 단백 ----------------------------------------------------------
    "ING.soy_protein_isolate":          (1.0, 3.5,   "유화·기포·바디. 3.5% 넘으면 콩 오프노트"),
    "ING.pea_protein_isolate":          (1.0, 3.5,   "대체 식물단백. 오프노트는 대두보다 강한 편"),
    # ---- 안정제 --------------------------------------------------------
    "ING.locust_bean_gum":              (0.10, 0.30, "구아와 시너지. 0.3% 넘으면 검성"),
    "ING.carrageenan":                  (0.01, 0.05, "2차 안정제 — 유청분리 방지용 극소량"),
    "ING.lambda_carrageenan":           (0.01, 0.05, "같은 역할. 겔화 안 하는 형"),
    "ING.xanthan_gum":                  (0.05, 0.20, "온톨로지 limitations: '> ~0.5% -> slimy/stringy'. 그보다 훨씬 낮게 잡음"),
    "ING.cmc":                          (0.10, 0.30, "점도·수분결합"),
    "ING.gellan_gum":                   (0.02, 0.10, "극소량 구조. 과하면 부서지는 겔"),
    "ING.modified_starch":              (1.0, 4.0,   "바디·fat replacer. 과하면 전분 느낌"),
    "ING.anyaddy_an15":                 (0.10, 0.50, "HPMC. 오버런·용해저항·동결해동"),
    "ING.microcrystalline_cellulose":   (0.20, 1.00, "heat-shock 저항·fat-like"),
    # ---- 유화제 --------------------------------------------------------
    "ING.mono_diglycerides":            (0.10, 0.40, "아이스크림 표준 유화제"),
    "ING.dmg95":                        (0.05, 0.25, "저HLB. 총량 0.3% 안팎에서 고HLB와 비율 조절"),
    "ING.sucrose_ester_s1670":          (0.05, 0.25, "고HLB. DMG95 와 페어링"),
    "ING.sucrose_ester_s1170":          (0.05, 0.25, "중HLB 보조"),
    "ING.lecithin":                     (0.10, 0.50, "클린라벨 보조 유화"),
    "ING.soyacell":                     (0.10, 0.50, "클린라벨 보조 유화"),
    "ING.emulaid":                      (0.10, 0.50, "보조 유화"),
    "ING.rice_bran_emulsifier":         (0.50, 3.00, "현미호분추출분말 — 유화 겸 풍미. 음료 실측에서 1.2~2.5% 사용"),
    # ---- 벌킹 · 섬유 ----------------------------------------------------
    "ING.inulin":                       (2.0, 8.0,   "섬유·fat replacer. 과하면 소화 불편"),
    "ING.polydextrose":                 (2.0, 8.0,   "벌킹·약한 FPD. 같은 이유로 상한"),
    "ING.resistant_maltodextrin":       (2.0, 8.0,   "가용성 섬유. 당류 미산입"),
    "ING.maltodextrin":                 (2.0, 8.0,   "고형분. GI 유의"),
    "ING.dextrin":                      (2.0, 8.0,   "고형분"),
    # ---- 풍미 ----------------------------------------------------------
    "ING.vanilla_extract":              (0.10, 0.60, "기본 향"),
    "ING.brown_rice_extract_powder":    (0.50, 3.00, "쌀 풍미 보강"),
    "ING.salt":                         (0.05, 0.20, "풍미증진. 0.2% 넘으면 짠맛이 인지된다"),
    "ING.strawberry_puree":             (5.0, 15.0,  "딸기 변형 시. 수분·당을 동반"),
    "ING.strawberry_artificial":        (0.05, 0.30, "딸기 변형 시"),
}

# 제한 등급 — 쓰지 말자는 뜻이 아니라 목표와 상충한다는 뜻이다. 그래도 쓸
# 경우를 대비해 경계는 둔다. 경계가 없으면 propose 가 무제한으로 밀어 넣는다.
SEED_RESTRICTED = {
    "ING.sunflower_oil":            (2.0, 8.0,   "산화 취약 — 산화취 위험. 고올레산형으로 대체 권장"),
    "ING.sucrose":                  (1.0, 6.0,   "당류. 저당 목표와 상충하나 FPD·바디 목적 최소량은 필요할 수 있다"),
    "ING.glucose_syrup":            (1.0, 6.0,   "당류. 같은 이유"),
    "ING.dextrose":                 (1.0, 5.0,   "당류. FPD 가 설탕보다 강해 소량으로도 효과"),
    "ING.rice_syrup":               (1.0, 6.0,   "당류(쌀조청)"),
    "ING.rice_protein":             (0.5, 2.0,   "가용성 낮고 그릿티 — 대두단백으로 대체 결론(HANDOFF)"),
    "ING.polysorbate_80":           (0.02, 0.08, "매우 강력하나 라벨 이슈. 쓴다면 극소량"),
}
SEED.update({k: (a, b, "제한 등급 · " + c) for k, (a, b, c) in SEED_RESTRICTED.items()})


def main(force=False):
    t = palette.load(PROFILE)
    rows, filled, skipped, unknown = [], 0, 0, []
    seen = set()
    for r in t.rows:
        g = r["온톨로지ID"]
        seen.add(g)
        d = dict(r)
        if g in SEED and r["등급"] in ("필수", "권장", "옵션", "제한"):
            has = r["하한"] is not None and r["상한"] is not None
            if has and not force:
                skipped += 1
            else:
                lo, hi, why = SEED[g]
                d["하한"], d["상한"] = lo, hi
                d["범위근거"] = f"{BASIS} · {why}"
                filled += 1
        rows.append(d)
    unknown = [g for g in SEED if g not in seen]

    palette.save_rows(PROFILE, rows)
    print(f"채움 {filled}종 · 기존값 유지 {skipped}종")
    if unknown:
        print(f"표에 없는 ID {len(unknown)}종: {unknown}")

    t2 = palette.load(PROFILE)
    s = t2.status()
    print(f"결과: 쓸 수 있는 재료 {s['usable']} · 범위 입력 {s['with_range']} · 미입력 {s['missing']}")
    bad = t2.bad_ranges()
    if bad:
        print(f"!! 상한<=하한 {bad}")
    miss = t2.missing_ranges()
    if miss:
        print(f"아직 비어 있는 것: {[g.replace('ING.','') for g in miss]}")


if __name__ == "__main__":
    main(force="--force" in sys.argv)
