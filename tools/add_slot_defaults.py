# -*- coding: utf-8 -*-
"""
기능 태그(FT.*)에 한글 이름과 표준 사용량을 넣는다.

왜 필요한가
-----------
선례가 없는 제형은 팔레트 표가 비어 있다. 그렇다고 사용자를 막아서는 안 된다 —
처음 만드는 사람이야말로 이 도구가 필요한 사람이다. 온톨로지에는 어떤 재료가
어떤 축을 움직이는지 다 들어 있으므로, 재료 후보는 실측 없이도 뽑을 수 있다.

없는 것은 **얼마나 쓰는가** 하나다. 재료의 limitations 는 자유 서술이라
(38종 중 % 수치가 글에 들어 있는 것이 3종) 기계가 읽지 못한다(G5). 그래서
기능군마다 통상 사용량을 둔다. 배합을 처음 잡을 때 배합가가 하는 일과 같다.

이 값은 **출발점이지 근거가 아니다.** 실측이 들어오면 build_palette 가 실제
사용 범위로 덮어쓴다. 전문가 화면 ④ 팔레트에서 검토·수정할 수 있다.

제형이 정하는 것은 제형에서 가져온다
------------------------------------
유지와 고형분은 제형에 따라 자릿수가 다르다(음료 0.01~15%, 소스 5~75%).
이건 기능군 표준값으로 뭉갤 수 없고, 실제로 STRUCTURE 가 정의 파라미터로 이미
가지고 있다 — P.oil_phase_fraction, P.fat_content, P.solids_volume_fraction.
v2adapter.slot_bounds() 가 그쪽을 먼저 보고, 없을 때만 아래 표로 내려온다.

    python tools/add_slot_defaults.py           # 넣기
    python tools/add_slot_defaults.py --check   # 빠진 태그만 보고
"""
from __future__ import annotations

import glob
import io
import os
import sys

import yaml

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAYERS = os.path.join(HERE, "ontology_v2", "layers")

# 기능군: (한글 이름, 통상 사용량 하한 %, 상한 %)
#
# 상한은 "이 이상 쓰면 그 기능이 아니라 결함이 된다" 는 선이다. 검류 1%,
# 유화제 1.5%, 보존료 0.5% 처럼 좁은 것은 그 자체가 강한 제약이고, 감미료
# 25%, 건더기 30% 처럼 넓은 것은 제품이 결정할 몫이 크다는 뜻이다.
SLOTS = {
    "FT.acidulant":          ("산미료", 0.0, 2.0),
    "FT.aroma_oil":          ("비정제 향미유", 0.0, 3.0),
    "FT.aromatic_allium":    ("향신 채소 (마늘·양파류)", 0.0, 8.0),
    "FT.aw_depressant":      ("수분활성 저하제", 0.0, 20.0),
    "FT.bulking_agent":      ("벌킹제 (증량)", 0.0, 15.0),
    "FT.colorant":           ("착색료", 0.0, 1.0),
    "FT.emulsifier":         ("유화제", 0.0, 1.5),
    "FT.fat_replacer":       ("지방 대체재", 0.0, 5.0),
    "FT.fat_source":         ("유지 (지방원)", 0.0, 20.0),
    "FT.fermented_paste":    ("발효 장류", 0.0, 20.0),
    "FT.firming_agent":      ("경화제 (2가 양이온)", 0.0, 0.5),
    "FT.flavorant":          ("향료·풍미재", 0.0, 3.0),
    "FT.fpd_agent":          ("빙점 강하제", 0.0, 10.0),
    "FT.milk_protein":       ("유단백 (무지유고형분)", 0.0, 12.0),
    "FT.mineral_fortifier":  ("미네랄 강화제", 0.0, 1.0),
    "FT.particulate":        ("분산 고형분 (건더기)", 0.0, 30.0),
    "FT.preservative":       ("보존료", 0.0, 0.5),
    "FT.protein":            ("기능성 단백", 0.0, 8.0),
    "FT.pungent_principle":  ("매운맛 성분", 0.0, 5.0),
    "FT.stabilizer":         ("안정제", 0.0, 1.0),
    "FT.sweetener":          ("감미료·당류", 0.0, 25.0),
    "FT.thickener":          ("증점제 (하이드로콜로이드)", 0.0, 1.0),
    "FT.umami_source":       ("감칠맛 재료", 0.0, 10.0),
    "FT.weighting_agent":    ("비중 조절제", 0.0, 0.3),
}

BASIS = ("선례가 없을 때 쓰는 기능군 통상 사용량. 실측이 들어오면 덮어쓴다. "
         "재료의 limitations 가 자유 서술이라 기계가 읽지 못해 둔 값이다(G5).")


def _q(s):
    return '"' + str(s).replace('"', '\\"') + '"'


def main(check=False):
    files = sorted(glob.glob(os.path.join(LAYERS, "layerC2_*.yaml")))
    seen, added = set(), 0

    for path in files:
        doc = yaml.safe_load(io.open(path, encoding="utf-8")) or {}
        here = {}
        for key in ("function_tags", "function_tags_ext"):
            for t in doc.get(key) or []:
                here[t["id"]] = t
        if not here:
            continue
        seen |= set(here)
        if check:
            continue

        lines = io.open(path, encoding="utf-8").read().splitlines(True)
        out = []
        for ln in lines:
            out.append(ln)
            s = ln.rstrip("\n")
            body = s.lstrip()
            if not body.startswith("- id: FT."):
                continue
            tid = body[len("- id: "):].strip().strip("'\"")
            if tid not in SLOTS or tid not in here:
                continue            # scope 확장 태그(FT.*_scope)는 슬롯이 아니다
            if here[tid].get("ko"):
                continue
            ind = " " * (len(s) - len(body) + 2)
            ko, lo, hi = SLOTS[tid]
            out.append(f"{ind}ko: {_q(ko)}\n")
            out.append(f"{ind}typical_use_pct: [{lo:g}, {hi:g}]\n")
            out.append(f"{ind}typical_use_basis: {_q(BASIS)}\n")
            added += 1
        io.open(path, "w", encoding="utf-8", newline="\n").write("".join(out))

    missing = set(SLOTS) - seen
    extra = {t for t in seen if t not in SLOTS and "_scope" not in t}
    if missing:
        print("표에는 있는데 온톨로지에 없는 태그:", sorted(missing))
    if extra:
        print("온톨로지에는 있는데 표에 없는 태그:", sorted(extra))
    if not missing and not extra:
        print(f"점검 통과 — 기능군 {len(SLOTS)}개 모두 온톨로지와 맞음")
    if not check:
        print(f"ko + typical_use_pct 를 태그 {added}개에 삽입")
    return 1 if (missing or extra) else 0


if __name__ == "__main__":
    sys.exit(main(check="--check" in sys.argv))
