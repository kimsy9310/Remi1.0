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

되돌리기·범위 고치기 (2026-09-12)
  --tidy 는 아래 TIDY 절의 결정을 적용한다 - 프로파일 빼기 · APP 이름 되돌리기 ·
  파라미터 범위 확정. 같은 파일(S2 · 카드 · 등록부)을 반대 방향으로 만지므로
  여기 둔다. 두 번 돌려도 이미 된 것은 건너뛴다.

    python tools/add_application.py --tidy            # 무엇이 바뀌나
    python tools/add_application.py --tidy --write
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
#
# dose_parent (2026-09-11): INGREDIENT 엣지에는 용량이 들어 있어 (FT.thickener ->
# 점도가 소스 strong · 음료 medium) 부모 SC 로 올릴 수 없다. 새 용도가 용량 면에서
# 어느 기존 용도의 하위인지 적으면 그 잎 스코프를 물려받는다. R-1(물리)은 부모
# SC 에서 온다. 베끼지도, 크기를 고르지도 않는다.
# ---------------------------------------------------------------------------
NEW = [
    # 2026-09-11 (b) 에 beverage 를 cloud / milk 로 갈랐다가 09-12 에 되돌렸다 (TIDY 절).
    # 유음료는 SC.emulsion.ow x APP.beverage 에 ING.milk 가 든 제품이지 별도 APP 이
    # 아니다 - CLAUDE.md "제품의존은 없다". 음료 프로파일 하나가 클라우드와 유음료를
    # 다 담도록 범위를 넓혔다.
    dict(key="dressing", app="APP.dressing", sibling="sauce_ow",
         sc="SC.emulsion.ow", dot="SC.emulsion.ow.dressing", dose_parent="SC.emulsion.ow.sauce",
         label="Oil-in-water emulsion dressing",
         ko_label="수중유 에멀전 드레싱",
         ko_def="연속상이 물이고 기름 방울이 분산된 두 상(相) 계. 소스와 같은 구조이나 "
                "따라 붓거나 버무리는 용도라 흐름성이 앞서고, 산미가 정체성인 경우가 많다.",
         definition="O/W emulsion used to coat or toss; same structure as sauce but "
                    "pourability leads and acidity is often the identity.",
         required=["FT.fat_source", "FT.emulsifier", "FT.acidulant"]),
    dict(key="dip", app="APP.dip", sibling="sauce_ow",
         sc="SC.emulsion.ow", dot="SC.emulsion.ow.dip", dose_parent="SC.emulsion.ow.sauce",
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
]

# 보류 (2026-09-12 사용자 결정). NEW 에 있으면 --write 가 다시 만들므로 여기 둔다.
# 국·찌개는 제형이 아니라 음식이고, 건더기(>=5 mm 조각)는 particle 로 잴지부터 안 정해졌다.
HELD = [
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


def find_sibling(S, key, app=None):
    for sp in S["structure_profiles"]:
        if (app and sp.get("application") == app) or            sp.get("source_file", "").endswith(f"{key}.yaml") or \
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


# ---------------------------------------------------------------------------
# TIDY (2026-09-12) - 사용자 결정. --tidy 로 적용.
#   * beverage_milk 삭제, beverage_cloud -> beverage 되돌림. 재 보니 분리가 실어 나른
#     것은 범위 두 행뿐이었다 (카드는 active_in 만 다르고, INGREDIENT 25건·RELATION
#     12건 모두 가족 스코프에만 걸려 있었다).
#   * soup 삭제 (보류. 사양은 HELD 에).
#   * dressing · dip · condiment 와 부모(sauce · beverage) 범위 확정. 자식 범위는
#     부모 안에 있어야 하므로 부모 행부터 적는다.
# ---------------------------------------------------------------------------
TIDY_REMOVE = ["beverage_milk", "soup"]
TIDY_RENAME = dict(key="beverage_cloud", new_key="beverage",
                   app="APP.beverage.cloud", new_app="APP.beverage",
                   label="Oil-in-water emulsion cloud beverage", new_label="Oil-in-water emulsion beverage",
                   ko_label="수중유 에멀전 클라우드 음료", new_ko_label="수중유 에멀전 음료")
CONFIRMED = "literature; confirmed by user 2026-09-12"
# (application, parameter, {field: value})
TIDY_RANGES = [
    # ---- beverage (부모): 클라우드 + 유음료를 한 프로파일이 담는다
    ("APP.beverage", "P.oil_phase_fraction", dict(
        range_basis="Flavor/cloud emulsions carry 10-100 ppm oil in the drink; milk-type beverages "
                    "(ING.milk, plant milks) 0.1-4% fat, cream-added up to 5%. Which one it is comes "
                    "from the ingredients, not the application. High phi belongs to sauce class.")),
    ("APP.beverage", "P.droplet_size_d32", dict(
        plausible_range="0.1 - 2.0 (cloud emulsions 0.2-0.5; homogenised milk-type 0.3-0.8, plant milks up to ~2)",
        range_basis="Sub-micron droplets resist creaming and give stable cloud; milk-type tolerates up to ~2 um "
                    "because protein and higher continuous-phase viscosity slow creaming; >2 um rings within shelf life.",
        range_source="literature; widened 2026-09-12 to cover milk-type (was 0.1-1.0 cloud-only)",
        range_confidence="medium")),
    ("APP.beverage", "P.pH", dict(
        plausible_range="2.8 - 7.2",
        range_basis="Acidified cloud beverages (juice, carbonated) 2.8-3.8; milk-type neutral 6.2-7.2. "
                    "Two stability regimes (electrostatic vs protein-stabilised), set by the ingredients.",
        range_source="literature 2026-09-12", range_confidence="medium")),
    ("APP.beverage", "P.soluble_solids_brix", dict(
        plausible_range="0 - 15 degBx",
        range_basis="Zero-sugar soft drinks near 0; juice drinks and sodas 8-13; milk and plant milks 6-13.",
        range_source="literature 2026-09-12", range_confidence="medium")),
    ("APP.beverage", "P.apparent_viscosity", dict(
        plausible_range="0.001 - 0.05 Pa.s @50 1/s",
        range_basis="Water 0.001, milk 0.002-0.003, starch-bearing plant milks and thick drinkable products 0.01-0.05.",
        range_source="literature 2026-09-12", range_confidence="medium")),
    # ---- sauce (부모): 09-11 draft 네 행 확정
    ("APP.sauce", "P.apparent_viscosity", dict(range_source=CONFIRMED, range_confidence="medium")),
    ("APP.sauce", "P.yield_stress", dict(range_source=CONFIRMED, range_confidence="medium")),
    ("APP.sauce", "P.pH", dict(range_source=CONFIRMED, range_confidence="medium")),
    ("APP.sauce", "P.soluble_solids_brix", dict(range_source=CONFIRMED, range_confidence="medium")),
    # ---- dressing
    ("APP.dressing", "P.oil_phase_fraction", dict(
        plausible_range="0.05 - 0.60 (w/w)",
        range_basis="pourable: vinaigrette 30-50%, creamy pourable (ranch, caesar) 45-55%, low-fat 5-20%",
        range_source=CONFIRMED, range_confidence="medium")),
    ("APP.dressing", "P.droplet_size_d32", dict(range_source=CONFIRMED, range_confidence="medium")),
    ("APP.dressing", "P.apparent_viscosity", dict(range_source=CONFIRMED, range_confidence="medium")),
    ("APP.dressing", "P.yield_stress", dict(
        plausible_range="0 - 15 Pa",
        range_basis="little or no standing structure - runs off a spoon; creamy pourable dressings 5-15 Pa; "
                    "dip begins at 20",
        range_source=CONFIRMED, range_confidence="medium")),
    ("APP.dressing", "P.pH", dict(range_source=CONFIRMED, range_confidence="medium")),
    ("APP.dressing", "P.soluble_solids_brix", dict(
        plausible_range="5 - 30 degBx",
        range_basis="sweet styles (honey-mustard, oriental) reach 25-30; a refractometer reads poorly on "
                    "emulsions - calculate from the recipe",
        range_source=CONFIRMED, range_confidence="medium")),
    # ---- dip
    ("APP.dip", "P.oil_phase_fraction", dict(
        plausible_range="0.15 - 0.70 (w/w)",
        range_basis="sour-cream/yogurt dips 15-25%, mayonnaise-based dips (aioli-type) 60-70%; "
                    "0.75 is mayonnaise itself = sauce",
        range_source=CONFIRMED, range_confidence="medium")),
    ("APP.dip", "P.droplet_size_d32", dict(range_source=CONFIRMED, range_confidence="medium")),
    ("APP.dip", "P.apparent_viscosity", dict(range_source=CONFIRMED, range_confidence="medium")),
    ("APP.dip", "P.yield_stress", dict(
        plausible_range="20 - 150 Pa",
        range_basis="stands in the bowl, scoops - the axis that separates dip from dressing; "
                    "upper bound is the parent sauce's 150",
        range_source=CONFIRMED, range_confidence="medium")),
    ("APP.dip", "P.pH", dict(
        plausible_range="3.8 - 4.6",
        range_basis="milder than dressing; 4.6 is the shelf-stable safety line (LESSON.ph_safety). "
                    "Fresh refrigerated dips (sour cream, 4.6-5.0) sit outside this bound",
        range_source=CONFIRMED, range_confidence="medium")),
    ("APP.dip", "P.soluble_solids_brix", dict(range_source=CONFIRMED, range_confidence="medium")),
    # ---- condiment (paste)
    ("APP.condiment", "P.solids_volume_fraction", dict(range_source=CONFIRMED, range_confidence="medium")),
    ("APP.condiment", "P.particle_size_d50", dict(
        plausible_range="50 - 5000 micrometre",
        range_basis="ground chilli/grain 50-500 um; whole or coarse bean pieces in doenjang/ssamjang 2-5 mm",
        range_source=CONFIRMED, range_confidence="medium")),
    ("APP.condiment", "P.particle_size_d90", dict(range_source=CONFIRMED, range_confidence="medium")),
    ("APP.condiment", "P.pH", dict(range_source=CONFIRMED, range_confidence="medium")),
    ("APP.condiment", "P.salt_in_water_phase", dict(
        plausible_range="6 - 25 %",
        range_basis="concentrated, eaten in small amounts - the axis that separates condiment from soup; "
                    "low-salt gochujang ~4% salt / 45% moisture = ~9%",
        range_source=CONFIRMED, range_confidence="medium")),
    ("APP.condiment", "P.water_activity", dict(
        plausible_range="0.65 - 0.90",
        range_basis="fermented pastes sit at aw 0.75-0.85, well below the 0.93 C. botulinum line; no paste reaches 0.99",
        range_source=CONFIRMED, range_confidence="medium")),
    ("APP.condiment", "P.sedimentation_rate", dict(
        plausible_range="0 - 1 mm/day",
        range_basis="a paste is jammed / yield-stress-stabilised and does not sediment; not a failure axis here",
        range_source=CONFIRMED, range_confidence="medium")),
    ("APP.condiment", "P.serum_separation_index", dict(
        plausible_range="0 - 10 %",
        range_basis="syneresis (liquid weeping on the surface) occurs in fermented pastes but stays small",
        range_source=CONFIRMED, range_confidence="medium")),
    ("APP.condiment", "P.capsaicinoid_shu", dict(range_source=CONFIRMED, range_confidence="medium")),
]
REVIEWED = "reviewed 2026-09-12 - ranges confirmed (see range_source); rows without a range have none in the sibling either"
TIDY_STATUS = {"APP.dressing": REVIEWED, "APP.dip": REVIEWED, "APP.condiment": REVIEWED}
BEV_DEF = ("An O/W emulsion consumed as a liquid: oil or fat droplets dispersed in a drinkable aqueous phase, "
           "from dilute cloud emulsions (flavor/cloud oil at ppm-to-low-percent) to milk-type beverages "
           "(dairy or plant milk, 1-4% fat with protein and solids). Key quality is uniform opacity with no "
           "visible oil ring, creaming or sediment; low viscosity. Whether it is a cloud drink or a milk "
           "beverage is set by the ingredients (e.g. ING.milk), not by the application.")
BEV_KO_DEF = ("마실 수 있는 수상에 기름·지방 방울이 분산된 O/W 에멀전이다. 향유·백탁유가 ppm~수 % 든 묽은 "
              "클라우드 음료부터 지방 1~4% 에 단백질·고형분이 함께 든 유음료·식물성 밀크까지 한 제형이다. "
              "핵심 품질은 기름 고리·크리밍·침전 없이 고르게 뿌연 상태를 유지하는 것이며 점도가 낮다. "
              "클라우드 음료인지 유음료인지는 용도가 아니라 재료(예: ING.milk)가 정한다.")


def _yscalar(v):
    """YAML 한 줄 스칼라. 따옴표는 yaml 이 필요할 때만 붙인다."""
    out = yaml.safe_dump(v, allow_unicode=True, width=10 ** 6).strip()
    return out[:-4].rstrip() if out.endswith("\n...") else out.split("\n...")[0]


def _split_blocks(lines):
    """S2 텍스트를 프로파일 블록으로 가른다 -> [[start, end, app]]. start 는 바로 앞의
    '# ---- ' 머리 주석과 빈 줄을 포함한다."""
    starts = [i for i, ln in enumerate(lines) if ln.startswith("- structure_class:")]
    blocks = []
    for n, i in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        while end > i and (lines[end - 1].startswith("# ---- ") or not lines[end - 1].strip()):
            end -= 1
        app = None
        for ln in lines[i:end]:
            m = re.match(r"^  application: (\S+)", ln)
            if m:
                app = None if m.group(1) == "null" else m.group(1)
                break
        blocks.append([i, end, app])
    for n in range(1, len(blocks)):
        s = blocks[n][0]
        while s > blocks[n - 1][1] and (lines[s - 1].startswith("# ---- ") or not lines[s - 1].strip()):
            s -= 1
        blocks[n][0] = s
    return blocks


def _set_param_fields(lines, pid, fields, log):
    """파라미터 소블록의 필드를 바꾸거나, 없으면 id 줄 뒤에 넣는다. 바뀐 수를 돌려준다."""
    try:
        i = next(k for k, ln in enumerate(lines) if ln.rstrip() == f"  - id: {pid}")
    except StopIteration:
        log.append(f"      !! {pid} 없음"); return 0
    j = i + 1
    while j < len(lines) and lines[j].startswith("    "):
        j += 1
    changed = 0
    for f, v in fields.items():
        new = f"    {f}: {_yscalar(v)}"
        cur = next((k for k in range(i + 1, j) if re.match(rf"^    {f}:", lines[k])), None)
        if cur is not None:
            old = yaml.safe_load(lines[cur][len(f) + 6:])
            if old == v:
                continue
            log.append(f"      {pid}.{f}: {old!s} -> {v!s}")
            lines[cur] = new
        else:
            log.append(f"      {pid}.{f}: (없음) -> {v!s}")
            lines.insert(i + 1, new); j += 1
        changed += 1
    return changed


def _groupby(rows):
    out = {}
    for app, pid, fields in rows:
        out.setdefault(app, []).append((pid, fields))
    return out.items()


def tidy(write=False):
    print("=" * 70)
    print("  STRUCTURE 정리 (2026-09-12)" + ("" if write else "   (미리보기)"))
    print("=" * 70)
    s_lines = io.open(S_FILE, encoding="utf-8").read().split("\n")
    loader = io.open(LOADER, encoding="utf-8").read()
    n_changes = 0
    blocks = _split_blocks(s_lines); by_app = {b[2]: b for b in blocks}

    # ---- 1 프로파일 빼기
    for key in TIDY_REMOVE:
        spec = next((d for d in NEW + HELD if d["key"] == key), None)
        app = spec["app"] if spec else "APP." + key.replace("_", ".")
        card = os.path.join(LAYERS, f"layerM_cards_{key}.yaml")
        reg = f"    '{key}': dict("
        b = by_app.get(app)
        have_c, have_r = os.path.exists(card), reg in loader
        if not (b or have_c or have_r):
            print(f"  삭제 {key:<14} 이미 없음"); continue
        print(f"  삭제 {key:<14} S2 {('%d줄' % (b[1] - b[0])) if b else '-':>6} · "
              f"카드 {'있음' if have_c else '-'} · 등록 {'있음' if have_r else '-'}")
        n_changes += 1
        if b:
            s_lines[b[0]:b[1]] = []
            blocks = _split_blocks(s_lines); by_app = {x[2]: x for x in blocks}
        if have_c and write:
            os.remove(card)
        if have_r:
            a = loader.index(reg); e = loader.index("}),\n", a) + len("}),\n")
            loader = loader[:a] + loader[e:]

    # ---- 2 APP 이름 되돌리기
    R = TIDY_RENAME
    old_card = os.path.join(LAYERS, f"layerM_cards_{R['key']}.yaml")
    new_card = os.path.join(LAYERS, f"layerM_cards_{R['new_key']}.yaml")
    b = by_app.get(R["app"])
    reg = f"    '{R['key']}': dict("
    if b or os.path.exists(old_card) or reg in loader:
        print(f"  이름 {R['app']} -> {R['new_app']}  ({R['key']} -> {R['new_key']}: S2 {'있음' if b else '-'} · "
              f"카드 {'있음' if os.path.exists(old_card) else '-'} · 등록 {'있음' if reg in loader else '-'})")
        n_changes += 1
        if b:
            for k in range(b[0], b[1]):
                ln = s_lines[k]
                if ln.startswith("  application: " + R["app"]):
                    s_lines[k] = (f"  application: {R['new_app']}   # 2026-09-12: 09-11 의 cloud/milk 분리를 되돌렸다. "
                                  f"유음료는 ING.milk 가 정한다 (tools/add_application.py --tidy)")
                elif ln == f"  label: {R['label']}":
                    s_lines[k] = f"  label: {R['new_label']}"
                elif ln.strip() == f"label: '{R['ko_label']}'":
                    s_lines[k] = f"    label: '{R['new_ko_label']}'"
            k_ko = next(k for k in range(b[0], b[1]) if s_lines[k].startswith("    definition: "))
            s_lines[k_ko] = "    definition: " + _yscalar(BEV_KO_DEF)
            k_en = next(k for k in range(b[0], b[1]) if s_lines[k].startswith("  definition: "))
            k_end = next(k for k in range(k_en + 1, b[1]) if not s_lines[k].startswith("    "))
            s_lines[k_en:k_end] = ["  definition: " + _yscalar(BEV_DEF)]
            blocks = _split_blocks(s_lines); by_app = {x[2]: x for x in blocks}
        if os.path.exists(old_card):
            t = io.open(old_card, encoding="utf-8").read()
            t = t.replace(f"SC.emulsion.ow|{R['app']}", f"SC.emulsion.ow|{R['new_app']}")
            t = t.replace(f"  profile: {R['label']}", f"  profile: {R['new_label']}")
            print(f"      카드 {os.path.basename(old_card)} -> {os.path.basename(new_card)}  (active_in {t.count(R['new_app'])}곳)")
            if write:
                io.open(new_card, "w", encoding="utf-8", newline="\n").write(t)
                os.remove(old_card)
        if reg in loader:
            a = loader.index(reg); e = loader.index("}),\n", a) + len("}),\n")
            c = loader.rfind("\n    # 2026-09-11: 'beverage' 를 beverage_cloud", 0, a)
            if c != -1 and loader[c + 1:a].count("\n") <= 5:
                a = c + 1
            loader = (loader[:a]
                      + "    # 2026-09-11 에 beverage_cloud / beverage_milk 로 갈랐다가 09-12 에 되돌렸다.\n"
                      + "    # 유음료는 SC.emulsion.ow x APP.beverage 에 ING.milk 가 든 제품이지 별도 APP 이\n"
                      + "    # 아니다 - CLAUDE.md '제품의존은 없다'. 음료 프로파일 하나가 클라우드와 유음료를\n"
                      + "    # 다 담도록 범위를 넓혔다 (tools/add_application.py --tidy).\n"
                      + f"    '{R['new_key']}': dict(\n"
                      + f"        cards=['layerM_cards_{R['new_key']}.yaml'],\n"
                      + "        scopes={'any', 'SC.emulsion.ow', 'SC.emulsion.ow.beverage', 'SC.emulsion.ow|APP.beverage'}),\n"
                      + loader[e:])
    else:
        print(f"  이름 {R['new_app']}  이미 됨")

    # ---- 3 범위
    for app, group in _groupby(TIDY_RANGES):
        b = by_app.get(app)
        if not b:
            print(f"  범위 {app:<15} !! 프로파일 없음"); continue
        seg = s_lines[b[0]:b[1]]
        log, n = [], 0
        for pid, fields in group:
            n += _set_param_fields(seg, pid, fields, log)
        st = TIDY_STATUS.get(app)
        if st:
            k = next((i for i, ln in enumerate(seg) if ln.startswith("  status: ")), None)
            if k is not None and seg[k] != "  status: " + _yscalar(st):
                log.append(f"      status: {seg[k][10:]} -> {st[:30]}..."); seg[k] = "  status: " + _yscalar(st); n += 1
        print(f"  범위 {app:<15} 바뀌는 필드 {n}")
        for ln in log:
            print(ln)
        if n:
            s_lines[b[0]:b[1]] = seg
            blocks = _split_blocks(s_lines); by_app = {x[2]: x for x in blocks}
            n_changes += n

    if not n_changes:
        print("\n  바꿀 것 없음"); return 0
    if not write:
        print("\n  실제로 고치려면: python tools/add_application.py --tidy --write")
        return 0
    io.open(S_FILE, "w", encoding="utf-8", newline="\n").write("\n".join(s_lines).rstrip("\n") + "\n")
    io.open(LOADER, "w", encoding="utf-8", newline="\n").write(loader)
    print(f"\n  썼다: {os.path.basename(S_FILE)} · {os.path.basename(LOADER)} · 카드 파일")
    return 0


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
        sib = find_sibling(S, spec["sibling"], spec.get("sibling_app"))
        entry = derive_entry(spec, sib)
        card_text, ident = derive_cards(spec, spec["sibling"])
        scopes = {"any", spec["sc"], spec["dot"], ident}
        if spec.get("dose_parent"):
            scopes.add(spec["dose_parent"])
        scopes |= set(spec.get("family") or [])
        n = reach_count(scopes)
        print(f"  {spec['key']:<10} <- {spec['sibling']:<11} 파라미터 {len(entry['parameters']):>2} · "
              f"카드 {card_text.count('- term_id:'):>2} · 도달축 {n}")
        new_entries.append(entry)
        new_cards.append((spec["key"], card_text))
        reg_lines.append(
            f"    '{spec['key']}': dict(   # 2026-09-11 tools/add_application.py 로 {spec['sibling']} 에서 파생\n"
            f"        cards=['layerM_cards_{spec['key']}.yaml'],\n"
            f"        scopes={{'any', '{spec['sc']}', "
            + (f"'{spec['dose_parent']}', " if spec.get("dose_parent") else "")
            + "".join(f"'{s}', " for s in (spec.get("family") or []))
            + f"'{spec['dot']}', '{ident}'}}),\n")
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
    if "--tidy" in sys.argv:
        sys.exit(tidy(write="--write" in sys.argv))
    sys.exit(main(write="--write" in sys.argv))
