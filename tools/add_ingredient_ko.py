# -*- coding: utf-8 -*-
"""
재료(ING.*)에 한글 이름을 넣는다.

사용자 화면 ③ 이 Water / Salt / Gochujang 으로 나오고 있었다. 118종 중 이름에
한글이 들어 있던 것은 12종뿐이다. 슬롯 이름(FT.ko)과 축 이름(LEXICON 의 ko)은
한글인데 정작 고르는 대상이 영문이면 화면이 반만 읽힌다.

이름은 EFFECT 의 재료 옆에 둔다 — 축 이름을 렉시콘에 두는 것과 같은 이유다.
앱은 label 대신 ko 를 먼저 본다(V2Ontology.ing_label).

괄호 안의 규격(HLB, 등급, 지방 함량)은 이름의 일부로 남긴다. 배합가가 재료를
고를 때 실제로 구분하는 정보이고, 빼면 자당지방산에스테르 세 종이 같은 이름이
되어 버린다.

    python tools/add_ingredient_ko.py           # 넣기
    python tools/add_ingredient_ko.py --check   # 빠진 재료만 보고
"""
from __future__ import annotations

import glob
import io
import os
import sys

import yaml

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAYERS = os.path.join(HERE, "ontology_v2", "layers")

KO = {
    # --- 감미료
    "ING.acesulfame_k": "아세설팜칼륨",
    "ING.allulose": "알룰로스",
    "ING.aspartame": "아스파탐",
    "ING.dextrose": "포도당",
    "ING.erythritol": "에리스리톨",
    "ING.glucose_syrup": "물엿 (포도당 시럽)",
    "ING.high_intensity_sweetener": "고감미도 감미료",
    "ING.maesil_syrup": "매실청",
    "ING.rice_syrup": "쌀조청 (농축 쌀 추출액)",
    "ING.stevia_reb_a": "스테비아 (레바우디오사이드 A)",
    "ING.sucralose": "수크랄로스",
    "ING.sucrose": "설탕",
    "ING.sugar_alcohol": "당알코올",
    # --- 유지
    "ING.canola_oil": "카놀라유",
    "ING.coconut_oil": "코코넛유",
    "ING.cream": "생크림 (유지방)",
    "ING.high_fat_powder": "고지방 분말유지",
    "ING.high_oleic_sunflower_oil": "고올레산 해바라기유",
    "ING.hydrogenated_palm_kernel_oil": "팜핵경화유",
    "ING.olive_oil_evoo": "엑스트라버진 올리브유",
    "ING.palm_oil": "정제 팜유",
    "ING.perilla_oil": "들기름",
    "ING.refined_coconut_oil": "정제 코코넛유",
    "ING.rice_bran_oil": "현미유",
    "ING.sesame_oil_toasted": "참기름",
    "ING.sunflower_oil": "해바라기유",
    "ING.prima_creamer": "프리마 크리머 (비건)",
    "ING.vegan_creamer": "비건 크리머 분말",
    # --- 유화제
    "ING.anyaddy_an15": "애니애디 AN15 (저점도 HPMC)",
    "ING.dmg95": "증류 모노글리세라이드 DMG95",
    "ING.egg_yolk": "난황",
    "ING.emulaid": "OSA 전분 유화제 (에멀에이드)",
    "ING.lecithin": "레시틴",
    "ING.mono_diglycerides": "모노·디글리세라이드",
    "ING.polysorbate_80": "폴리소르베이트 80",
    "ING.rice_bran_emulsifier": "미강 유화제",
    "ING.soyacell": "소야셀 (대두 유래 부분 유화제)",
    "ING.sucrose_ester": "자당지방산에스테르",
    "ING.sucrose_ester_s1170": "자당지방산에스테르 S-1170 (HLB 11)",
    "ING.sucrose_ester_s1670": "자당지방산에스테르 S-1670 (HLB 16)",
    # --- 증점·안정제
    "ING.arabic_gum": "아라비아검",
    "ING.carrageenan": "카라기난 (카파형)",
    "ING.carrageenan_semi_refined": "반정제 카라기난",
    "ING.cmc": "카복시메틸셀룰로스 (CMC)",
    "ING.gellan_gum": "젤란검",
    "ING.guar_gum": "구아검",
    "ING.iota_carrageenan": "이오타 카라기난",
    "ING.lambda_carrageenan": "람다 카라기난",
    "ING.locust_bean_gum": "로커스트빈검 (LBG)",
    "ING.microcrystalline_cellulose": "미결정셀룰로스 (MCC)",
    "ING.modified_starch": "변성전분",
    "ING.xanthan_gum": "잔탄검",
    # --- 벌킹·섬유
    "ING.dextrin": "덱스트린",
    "ING.inulin": "이눌린",
    "ING.maltodextrin": "말토덱스트린",
    "ING.polydextrose": "폴리덱스트로스",
    "ING.resistant_maltodextrin": "난소화성 말토덱스트린",
    # --- 단백
    "ING.pea_protein_isolate": "완두 분리단백",
    "ING.rice_protein": "쌀 단백",
    "ING.skim_milk_powder": "탈지분유",
    "ING.soy_protein_isolate": "대두 분리단백",
    "ING.whole_milk": "우유 (전지, 유지방 3.5%)",
    # --- 산미료·완충
    "ING.calcium_carbonate": "탄산칼슘",
    "ING.calcium_lactate": "젖산칼슘",
    "ING.citric_acid": "구연산",
    "ING.citric_acid_anhydrous": "구연산 (무수)",
    "ING.lactic_acid": "젖산",
    "ING.lemon_juice": "레몬즙",
    "ING.lime_juice": "라임즙",
    "ING.sodium_citrate": "구연산나트륨",
    "ING.vinegar_brewed": "양조식초",
    # --- 매운맛
    "ING.black_pepper": "후추",
    "ING.capsicum_oleoresin": "고추 올레오레진",
    "ING.cayenne_powder": "카옌 고춧가루",
    "ING.chili_dried_ancho": "안초 (건 포블라노)",
    "ING.chili_fresh_green": "풋고추 (청양·할라피뇨류)",
    "ING.chili_fresh_red": "홍고추 (생)",
    "ING.chipotle": "치포틀레 (훈연 건 할라피뇨)",
    "ING.gochugaru_coarse": "고춧가루 (굵은)",
    "ING.gochugaru_fine": "고춧가루 (고운)",
    "ING.habanero": "하바네로",
    "ING.jalapeno": "할라피뇨",
    "ING.ginger_fresh": "생강",
    "ING.ginger_powder": "생강 분말",
    # --- 발효·감칠맛
    "ING.doenjang": "된장",
    "ING.fish_sauce_anchovy": "멸치액젓",
    "ING.gochujang": "고추장",
    "ING.miso": "미소",
    "ING.msg": "글루탐산나트륨 (MSG)",
    "ING.oyster_sauce": "굴소스",
    "ING.soy_sauce_brewed": "양조간장",
    "ING.yeast_extract": "효모 추출물",
    # --- 향신 채소·건더기
    "ING.black_garlic": "흑마늘",
    "ING.cilantro": "고수",
    "ING.cumin": "커민",
    "ING.garlic_fresh": "생마늘",
    "ING.garlic_powder": "마늘 분말",
    "ING.garlic_roasted": "구운 마늘",
    "ING.onion_fresh": "양파",
    "ING.onion_powder": "양파 분말",
    "ING.oregano_mexican": "멕시칸 오레가노",
    "ING.paprika_smoked": "훈제 파프리카",
    "ING.paprika_sweet": "스위트 파프리카",
    "ING.shallot": "샬롯",
    "ING.tomatillo": "토마티요",
    "ING.tomato_diced": "다진 토마토",
    "ING.tomato_paste": "토마토 페이스트",
    # --- 향미
    "ING.coffee_extract": "커피 추출액",
    "ING.instant_coffee_powder": "인스턴트 커피 분말",
    "ING.strawberry_flavor_artificial": "딸기 합성향료",
    "ING.strawberry_puree": "딸기 퓨레",
    "ING.vanilla_extract": "바닐라 추출물",
    "ING.plant_extract": "식물 추출물",
    # --- 쌀 계열
    "ING.brown_rice_extract_powder": "현미 추출 분말",
    "ING.rice_extract": "쌀 농축액",
    # --- 그 밖
    "ING.potassium_sorbate": "소브산칼륨",
    "ING.salt": "소금",
    "ING.water": "물",
}


def _q(s):
    return '"' + str(s).replace('"', '\\"') + '"'


def main(check=False):
    files = sorted(glob.glob(os.path.join(LAYERS, "layerC2_*.yaml")))
    seen, added = set(), 0

    for path in files:
        doc = yaml.safe_load(io.open(path, encoding="utf-8")) or {}
        here = {}
        for key in ("ingredients", "ingredients_ext"):
            for g in doc.get(key) or []:
                here[g["id"]] = g
        if not here:
            continue
        seen |= {g for g in here if g in KO}
        if check:
            continue

        lines = io.open(path, encoding="utf-8").read().splitlines(True)
        out = []
        for ln in lines:
            out.append(ln)
            s = ln.rstrip("\n")
            body = s.lstrip()
            if not body.startswith("- id: ING."):
                continue
            gid = body[len("- id: "):].strip().strip("'\"")
            if gid not in KO or gid not in here or here[gid].get("ko"):
                continue
            ind = " " * (len(s) - len(body) + 2)
            out.append(f"{ind}ko: {_q(KO[gid])}\n")
            added += 1
        io.open(path, "w", encoding="utf-8", newline="\n").write("".join(out))

    # 온톨로지에 있는데 이름을 안 준 재료 (화면에 영문으로 나갈 것들)
    all_ings = set()
    for path in files:
        doc = yaml.safe_load(io.open(path, encoding="utf-8")) or {}
        for key in ("ingredients", "ingredients_ext"):
            for g in doc.get(key) or []:
                if not g.get("alias_of"):
                    all_ings.add(g["id"])
    missing = sorted(all_ings - set(KO))
    extra = sorted(set(KO) - all_ings)
    if missing:
        print(f"한글 이름이 없는 재료 {len(missing)}종:", missing[:10])
    if extra:
        print(f"표에만 있고 온톨로지에 없는 재료 {len(extra)}종:", extra[:10])
    if not missing and not extra:
        print(f"점검 통과 — 재료 {len(all_ings)}종 모두 한글 이름이 있음")
    if not check:
        print(f"ko 를 재료 {added}종에 삽입")
    return 1 if (missing or extra) else 0


if __name__ == "__main__":
    sys.exit(main(check="--check" in sys.argv))
