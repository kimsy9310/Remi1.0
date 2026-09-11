# -*- coding: utf-8 -*-
"""
STRUCTURE 에 용도(APP)를 늘린다 — 가장 가까운 기존 제형에서 파생해서.

왜 도구인가
  사용자 (2026-09-11): "Structure 의 APP 늘리자. 반드시 늘릴거야."
  지금 셋(beverage · sauce · dessert)뿐이라 "드레싱" 을 받으면 붙일 곳이 없다.
  제형 항목 하나는 파라미터 14개·축 16개짜리라 손으로 쓰면 오타와 누락이 생기고,
  또 늘릴 때마다 같은 일을 반복하게 된다.

무엇을 만드나 (APP 하나당)
  1 STRUCTURE 항목    layerS2_profiles.yaml 에 형제를 복사해 application · label ·
                      ko · definition · required_functions 를 바꿔 넣는다.
                      파라미터 범위는 형제 것을 그대로 쓰되 range_confidence: draft
                      로 표시한다 - 검토 전까지는 형제의 값이다.
  2 AXIS_CARD 파일    layerM_cards_<이름>.yaml. 형제 카드를 복사하고 active_in 만
                      새 정체성으로 바꾼다. 앵커 문장은 형제와 같다 - 드레싱의
                      "걸쭉함" 앵커가 소스와 다를 이유가 없다.
  3 등록              tests/loader_reference.py 의 PROFILES 에 한 줄.

무엇을 안 하나
  INGREDIENT 엣지를 복사하지 않는다. 새 APP 은 부모 SC 와 any 로 걸린 엣지만
  물려받는다. 잎(APP.sauce)에 걸린 엣지가 새 APP 에 안 닿는 것은 그 엣지가
  너무 낮은 곳에 적힌 탓이지(docs/식감_온톨로지_정리.md 1절), 여기서 베낄
  일이 아니다. 도달 수는 --check 가 보여준다.

    python tools/add_application.py            # 무엇이 생기고 몇 축에 닿는지
    python tools/add_application.py --write
"""
from __future__ import annotations

import copy
import io
import os
import re
import sys

import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAYERS = os.path.join(ROOT, "ontology_v2", "layers")
S_FILE = os.path.join(LAYERS, "layerS2_profiles.yaml")
LOADER = os.path.join(ROOT, "ontology_v2", "tests", "loader_reference.py")
sys.path[:0] = [os.path.join(ROOT, "engine")]

# ---------------------------------------------------------------------------
# 늘릴 용도. 형제(sibling)는 같은 SC 안에서 가장 가까운 기존 제형이다.
# spread 는 여기 없다 - 버터는 W/O, 크림치즈·잼은 겔이라 한 구조가 아니다.
# APP 이 아니라 SC 를 새로 세워야 하는 문제라 따로 여쭙는다.
# ---------------------------------------------------------------------------
NEW = [
    dict(key="dressing", app="APP.dressing", sibling="sauce_ow",
         sc="SC.emulsion.ow", dot="SC.emulsion.ow.dressing",
         label="Oil-in-water emulsion dressing",
         ko_label="수중유 에멀전 드레싱",
         ko_def="연속상이 물이고 기름 방울이 분산된 두 상(相) 계. 소스와 같은 구조이나 "
                "따라 붓거나 버무리는 용도라 흐름성이 앞서고, 산미가 정체성인 경우가 많다.",
         definition="O/W emulsion used to coat or toss; same structure as sauce but "
                    "pourability leads and acidity is often the identity.",
         required=["FT.fat_source", "FT.emulsifier", "FT.acidulant"]),
    dict(key="dip", app="APP.dip", sibling="sauce_ow",
         sc="SC.emulsion.ow", dot="SC.emulsion.ow.dip",
         label="Oil-in-water emulsion dip",
         ko_label="수중유 에멀전 딥",
         ko_def="연속상이 물이고 기름 방울이 분산된 두 상 계. 찍어 먹는 용도라 항복응력이 "
                "있어 흘러내리지 않으면서 부드럽게 떠져야 한다.",
         definition="O/W emulsion eaten by dipping; needs yield stress to cling to the "
                    "carrier yet scoop softly.",
         required=["FT.fat_source", "FT.emulsifier", "FT.thickener"]),
    dict(key="condiment", app="APP.condiment", sibling="suspension",
         sc="SC.suspension", dot="SC.suspension.condiment",
         label="Suspension condiment (paste)",
         ko_label="현탁 양념·페이스트",
         ko_def="녹지 않는 고체 입자가 연속 액상에 분산된 계. 고추장·된장·쌈장처럼 "
                "소량을 곁들이는 용도라 향과 짠맛이 진하고 떠먹거나 바른다.",
         definition="Solid-in-liquid dispersion used as a condiment or paste in small "
                    "amounts; concentrated in aroma and salt, spooned or spread.",
         required=["FT.particulate", "FT.thickener"]),
    dict(key="soup", app="APP.soup", sibling="suspension",
         sc="SC.suspension", dot="SC.suspension.soup",
         label="Suspension soup / stew",
         ko_label="현탁 수프·국",
         ko_def="녹지 않는 고체 입자가 연속 액상에 분산된 계. 국·찌개·수프처럼 "
                "그릇째 먹는 용도라 묽고 양이 많으며 건더기가 씹힌다.",
         definition="Solid-in-liquid dispersion eaten by the bowl; dilute, high volume, "
                    "with perceptible pieces.",
         required=["FT.particulate"]),
]


def load_s():
    return yaml.safe_load(io.open(S_FILE, encoding="utf-8"))


def find_sibling(S, key):
    for sp in S["structure_profiles"]:
        if sp.get("source_file", "").endswith(f"{key}.yaml") or \
           (key == "sauce_ow" and sp.get("application") == "APP.sauce") or \
           (key == "suspension" and sp.get("structure_class") == "SC.suspension" and not sp.get("application")):
            return sp
    raise KeyError(key)


def derive_entry(spec, sib):
    e = copy.deepcopy(sib)
    e["structure_class"] = spec["sc"]
    e["application"] = spec["app"]
    e["label"] = spec["label"]
    e["ko"] = {"label": spec["ko_label"], "definition": spec["ko_def"]}
    e["definition"] = spec["definition"]
    e["required_functions"] = spec["required"]
    e["derived_from"] = sib.get("label")
    e["derived_on"] = "2026-09-11"
    e["status"] = "DRAFT - ranges copied from sibling, review before trusting"
    for p in e.get("parameters") or []:
        p["range_confidence"] = "draft"
        p["range_source"] = f"copied from {sib.get('label')}"
    e.pop("source_file", None)
    return e


def derive_cards(spec, sib_key):
    src = os.path.join(LAYERS, f"layerM_cards_{sib_key}.yaml")
    text = io.open(src, encoding="utf-8").read()
    doc = yaml.safe_load(text)
    ident = f"{spec['sc']}|{spec['app']}"
    sib_ident = None
    for c in doc["measurement_cards"]:
        ai = c.get("active_in") or []
        if ai:
            sib_ident = ai[0]
            break
    # 텍스트로 바꾼다 - 앵커(&id)와 주석을 살리려고
    out = text.replace(sib_ident, ident) if sib_ident else text
    hdr = (f"# =============================================================================\n"
           f"# AXIS_CARD — {spec['label']}   (DRAFT, derived {spec['derived_on'] if 'derived_on' in spec else '2026-09-11'})\n"
           f"# -----------------------------------------------------------------------------\n"
           f"# {sib_key} 의 카드를 복사하고 active_in 만 {ident} 로 바꿨다.\n"
           f"# 앵커 문장은 형제와 같다 - 이 용도에서 다르게 읽혀야 할 축이 있으면 그 카드만\n"
           f"# 고친다. tools/add_application.py 가 만들었다.\n"
           f"# =============================================================================\n")
    out = re.sub(r"^  profile: .*$", f"  profile: {spec['label']}", out, count=1, flags=re.M)
    return hdr + out, ident


def reach_count(scopes):
    from formulator.v2adapter import V2Ontology
    o = V2Ontology()
    proxies = {}
    for r in o.stack["R"]["relations_proxy"]:
        if r["scope"] in scopes:
            proxies.setdefault(r["parameter"], []).append(r)
    axes = set()
    for g, d in o.ingredients.items():
        axes |= set(o._ref.effects_of(d, o.tags, proxies, scopes))
    return len(axes)


def main(write=False):
    S = load_s()
    have = {sp.get("application") for sp in S["structure_profiles"]}
    print("=" * 70)
    print("  STRUCTURE 에 용도 늘리기" + ("" if write else "   (미리보기)"))
    print("=" * 70)
    loader = io.open(LOADER, encoding="utf-8").read()
    new_entries, new_cards, reg_lines = [], [], []
    for spec in NEW:
        if spec["app"] in have:
            print(f"  {spec['key']:<10} 이미 있음 - 건너뜀")
            continue
        sib = find_sibling(S, spec["sibling"])
        entry = derive_entry(spec, sib)
        card_text, ident = derive_cards(spec, spec["sibling"])
        scopes = {"any", spec["sc"], spec["dot"], ident}
        n = reach_count(scopes)
        print(f"  {spec['key']:<10} <- {spec['sibling']:<11} 파라미터 {len(entry['parameters']):>2} · "
              f"카드 {card_text.count('- term_id:'):>2} · 도달축 {n}")
        new_entries.append(entry)
        new_cards.append((spec["key"], card_text))
        reg_lines.append(
            f"    '{spec['key']}': dict(   # 2026-09-11 tools/add_application.py 로 {spec['sibling']} 에서 파생\n"
            f"        cards=['layerM_cards_{spec['key']}.yaml'],\n"
            f"        scopes={{'any', '{spec['sc']}', '{spec['dot']}', '{ident}'}}),\n")
    if not new_entries:
        print("\n  늘릴 것 없음"); return 0
    if not write:
        print("\n  실제로 만들려면: python tools/add_application.py --write")
        return 0

    # ---- STRUCTURE: 텍스트 끝에 덧붙인다 (앵커·주석 보존)
    s_text = io.open(S_FILE, encoding="utf-8").read().rstrip("\n")
    add = yaml.safe_dump(new_entries, allow_unicode=True, sort_keys=False, width=100)
    add = "\n".join(("" if ln.startswith("- ") else "") + ln for ln in add.split("\n"))
    s_text += ("\n\n# ---- 2026-09-11 용도 확장 (tools/add_application.py). 전부 DRAFT ----\n" + add)
    io.open(S_FILE, "w", encoding="utf-8", newline="\n").write(s_text + "\n")
    # ---- cards
    for key, text in new_cards:
        io.open(os.path.join(LAYERS, f"layerM_cards_{key}.yaml"), "w",
                encoding="utf-8", newline="\n").write(text)
    # ---- PROFILES 등록
    anchor = "    'icecream': dict(\n"
    assert loader.count(anchor) == 1
    loader = loader.replace(anchor, "".join(reg_lines) + anchor)
    io.open(LOADER, "w", encoding="utf-8", newline="\n").write(loader)
    print(f"\n  STRUCTURE {len(new_entries)}항목 · 카드 파일 {len(new_cards)}개 · 등록 {len(reg_lines)}줄")
    return 0


if __name__ == "__main__":
    sys.exit(main(write="--write" in sys.argv))
