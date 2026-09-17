# -*- coding: utf-8 -*-
"""
스코프 대장 (scope index) — RULES C9. 온톨로지의 모든 성분(component)을 한 표로 뽑고
불변식 다섯을 검사한다.

왜 도구인가
  스코프는 성분에만 붙고(C1) 성분은 세 파일에 흩어져 있다 — INGREDIENT 엣지, P.axes(지금은
  PO 레코드), IN. 사람이 훑어서는 못 찾는다. 스코프의 어휘가 유한하고(목록 셋의 조합)
  붙는 자리가 셋뿐이므로 도구가 전부를 한 표로 뽑을 수 있고, 오류는 그 표 위의 불변식으로
  걸린다.

무엇을 읽나 (지금 파일 꼴 그대로 — 1.1 이관 전)
  INGREDIENT   FT.effects · ING.overrides · ING.flavor_profile   (scoped_to_structure_class, 점 표기)
  RELATION     relations_proxy (PO, = 미래의 P.axes) · relations_interaction (IN)
  STRUCTURE    제형 튜플 [SC, APP, ST] 과 core 축 목록
  점 표기 · 옛 필드 이름은 여기서 정본 꼴로 바꿔 읽는다(별칭표 ALIASES). 파일은 안 고친다.

불변식 (RULES C9)
  (i)   스코프의 모든 마디가 그 목록의 값이다
  (ii)  모든 성분이 제형 하나 이상에 맞는다 (고아 없음)
  (iii) 같은 (owner, to) 가 겹치는 스코프에서 부호가 다르면 좁은 쪽에 why(note) 가 있다
  (iv)  모든 제형의 모든 core 축에 재료→L 경로가 하나 이상 닿는다 (직접 또는 P 경유)
  (v)   (owner, to, scope) 는 유일하다

    python tools/scope_index.py            # 검사, 걸린 줄만 보여 준다
    python tools/scope_index.py --xlsx     # data/scope_index.xlsx 에 표 전체
"""
from __future__ import annotations

import collections
import os
import sys

import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAYERS = os.path.join(ROOT, "ontology_v2", "layers")
sys.path[:0] = [os.path.join(ROOT, "ontology_v2", "tests")]
import loader_reference as LR                                     # noqa: E402

OUT_XLSX = os.path.join(ROOT, "data", "scope_index.xlsx")

# ---------------------------------------------------------------------------
# 목록 셋 (RULES B4). structure_taxonomy.yaml 이 생기면 거기서 읽는다.
# ---------------------------------------------------------------------------
SC_VALUES = {"emulsion.ow", "suspension"}
APP_VALUES = {"beverage", "sauce", "dressing", "dip", "condiment", "dessert"}
ST_VALUES = {"frozen", "chilled", "ambient", "hot"}

# 점 표기 · 옛 스코프 → 정본 (RULES B3, 00장 이관표 #2)
ALIASES = {
    "SC.emulsion.ow.beverage": "SC.emulsion.ow|APP.beverage",
    "SC.emulsion.ow.sauce": "SC.emulsion.ow|APP.sauce",
    "SC.emulsion.ow.dressing": "SC.emulsion.ow|APP.dressing",
    "SC.emulsion.ow.dip": "SC.emulsion.ow|APP.dip",
    "SC.suspension.condiment": "SC.suspension|APP.condiment",
    "SC.frozen.ice_cream": "SC.emulsion.ow|APP.dessert|ST.frozen",
    "SC.emulsion.ow|APP.dessert|ST.frozen": "SC.emulsion.ow|APP.dessert|ST.frozen",
    "universal": "any",
}


def canon(scope):
    """스코프 문자열 → (sc, app, st) 튜플. 빈 칸은 None. any → (None, None, None)."""
    if scope is None or scope == "any":
        return (None, None, None)
    scope = ALIASES.get(scope, scope)
    sc = app = st = None
    for part in scope.split("|"):
        if part.startswith("SC."):
            sc = part[3:]
        elif part.startswith("APP."):
            app = part[4:]
        elif part.startswith("ST."):
            st = part[3:]
        else:
            return ("?" + part, None, None)
    return (sc, app, st)


def scope_str(t):
    if t == (None, None, None):
        return "any"
    return "|".join(p for p in (f"SC.{t[0]}" if t[0] else None, f"APP.{t[1]}" if t[1] else None,
                                f"ST.{t[2]}" if t[2] else None) if p)


def valid(t):
    """불변식 (i)."""
    sc, app, st = t
    return ((sc is None or sc in SC_VALUES) and (app is None or app in APP_VALUES)
            and (st is None or st in ST_VALUES))


def matches(scope_t, profile_t):
    """RULES B5: 스코프에 적힌 칸마다 제형의 그 칸과 같다."""
    return all(s is None or s == p for s, p in zip(scope_t, profile_t))


def written(t):
    return sum(1 for x in t if x is not None)


# ---------------------------------------------------------------------------
# 수집
# ---------------------------------------------------------------------------
def profiles(S):
    """제형 튜플 (sc, app, st) — ST 가 없으면 ambient (RULES B0). core 축도 같이."""
    out = {}
    for sp in S:
        sc = sp["structure_class"].split(".", 1)[1]
        app = sp.get("application")
        app = app.split(".", 1)[1] if app else None
        st = sp.get("state")
        st = st.split(".", 1)[1] if st else "ambient"
        t = (sc, app, st)
        core = {a["id"] for a in sp.get("relevant_attributes") or [] if a.get("tier") == "core"}
        ranges = {}
        for q in sp.get("parameters") or []:
            lo_hi = _range(q.get("plausible_range"))
            if lo_hi:
                ranges[q["id"]] = lo_hi
        out[t] = dict(label=sp["label"], core=core, ranges=ranges,
                      discriminators=set(sp.get("discriminators") or []))
    return out


def _range(text):
    """'0.05 - 0.60 (w/w)' → (0.05, 0.60). 숫자 둘을 못 찾으면 None."""
    import re
    if not isinstance(text, str):
        return None
    nums = re.findall(r"-?\d+(?:\.\d+)?", text.replace(",", ""))
    if len(nums) < 2:
        return None
    lo, hi = float(nums[0]), float(nums[1])
    return (lo, hi) if hi >= lo else None


def nearest(p, profs):
    """RULES B5-1: 같은 SC 의 제형 중 정의 파라미터 범위가 가장 많이 겹치는 것.
    점수 = 두 제형이 함께 가진 파라미터마다 구간 겹침 비율(0~1)의 합. 비교 대상 파라미터는
    두 제형의 discriminators 합집합, 없으면 함께 가진 범위 전부."""
    me = profs[p]
    best, best_score = None, 0.0
    for q, other in profs.items():
        if q == p or q[0] != p[0]:
            continue
        keys = (me["discriminators"] | other["discriminators"]) or (set(me["ranges"]) & set(other["ranges"]))
        score = 0.0
        for k in keys:
            a, b = me["ranges"].get(k), other["ranges"].get(k)
            if not a or not b:
                continue
            inter = max(0.0, min(a[1], b[1]) - max(a[0], b[0]))
            union = max(a[1], b[1]) - min(a[0], b[0])
            score += inter / union if union > 0 else 1.0
        if score > best_score:
            best, best_score = q, score
    return best, best_score


def components(stack):
    """모든 성분을 한 목록으로. 층 · 주인 · 대상 · 방향 · 세기 · 스코프(정본) · 원문 스코프 · why."""
    rows = []

    def add(layer, kind, owner, to, direction, magnitude, scope_raw, note, extra=""):
        raws = scope_raw if isinstance(scope_raw, list) else [scope_raw]
        for r in raws:
            t = canon(r)
            rows.append(dict(layer=layer, kind=kind, owner=owner, to=to, direction=direction,
                             magnitude=magnitude, scope=scope_str(t), scope_t=t,
                             scope_raw=r if r is not None else "(none)", why=(note or "").strip(),
                             extra=extra))

    for tid, tag in stack["tags"].items():
        for e in tag.get("effects") or []:
            if "direction" in e:
                add("INGREDIENT", "FT.effects", tid, e["to"], e["direction"], e.get("magnitude"),
                    e.get("scoped_to_structure_class", "any"), e.get("note"))
    for gid, ing in stack["ings"].items():
        for e in ing.get("overrides") or []:
            if isinstance(e, dict) and "direction" in e:
                add("INGREDIENT", "ING.overrides", gid, e["to"], e["direction"], e.get("magnitude"),
                    e.get("scoped_to_structure_class", "any"), e.get("note"))
        for e in ing.get("flavor_profile") or []:
            if isinstance(e, dict) and "direction" in e:
                add("INGREDIENT", "ING.flavor_profile", gid, e["to"], e["direction"],
                    e.get("magnitude") or e.get("intensity"),
                    e.get("scoped_to_structure_class", "any"), e.get("note"))
    for r in stack["R"]["relations_proxy"]:
        add("PARAMETER", "P.axes (PO)", r["parameter"], r["percept"],
            "increase" if r["monotone"] == "increasing" else "decrease",
            r.get("functional_form"), r.get("scope", "any"), r.get("note"), extra=r["id"])
    for r in stack["R"]["relations_interaction"]:
        kind = "IN.interactions" if r["effect"] in ("enhance", "suppress") else "IN.overlaps"
        direction = {"enhance": "increase", "suppress": "decrease"}.get(r["effect"], r["effect"])
        add("RELATION", kind, r["from"], r["to"], direction, r.get("magnitude"),
            r.get("scope", "any"), r.get("note"), extra=r["id"])
    return rows


# ---------------------------------------------------------------------------
# 불변식
# ---------------------------------------------------------------------------
def check(rows, profs):
    fails = collections.defaultdict(list)
    ptuples = list(profs)

    # (i) 없는 스코프
    for r in rows:
        if not valid(r["scope_t"]):
            fails["i"].append(f"{r['kind']:<18} {r['owner']} -> {r['to']}   scope {r['scope_raw']!r}")

    # (ii) 고아
    for r in rows:
        if valid(r["scope_t"]) and not any(matches(r["scope_t"], p) for p in ptuples):
            fails["ii"].append(f"{r['kind']:<18} {r['owner']} -> {r['to']}   scope {r['scope']}")

    # (v) 중복
    seen = collections.Counter((r["owner"], r["to"], r["scope"]) for r in rows)
    for (o, t, s), n in seen.items():
        if n > 1:
            fails["v"].append(f"{o} -> {t}   scope {s}   x{n}")

    # (iii) 겹치는 스코프에서 부호 반대, 좁은 쪽에 why 없음
    by = collections.defaultdict(list)
    for r in rows:
        by[(r["owner"], r["to"])].append(r)
    conflicts = []
    for (o, t), rs in by.items():
        dirs = {r["direction"] for r in rs}
        if len(dirs) < 2:
            continue
        for a in rs:
            for b in rs:
                if a is b or a["direction"] == b["direction"]:
                    continue
                overlap = any(matches(a["scope_t"], p) and matches(b["scope_t"], p) for p in ptuples)
                if not overlap:
                    continue
                narrow, wide = (a, b) if written(a["scope_t"]) >= written(b["scope_t"]) else (b, a)
                key = (o, t, narrow["scope"], wide["scope"])
                if key in {c[0] for c in conflicts}:
                    continue
                conflicts.append((key, narrow, wide))
    for key, narrow, wide in conflicts:
        o, t, ns, ws = key
        has_why = bool(narrow["why"])
        line = (f"{o} -> {t}   {narrow['direction']} @ {ns}  vs  {wide['direction']} @ {ws}"
                f"   {'why 있음' if has_why else '!! why 없음'}")
        fails["iii" if not has_why else "iii-ok"].append(line)

    # (iv) 구멍 — 제형의 core 축마다 재료→L 경로
    # 직접: INGREDIENT 성분 to == axis, 스코프 맞음. 경유: INGREDIENT to == P 이고 P.axes 가 axis 로, 둘 다 맞음
    ing_rows = [r for r in rows if r["layer"] == "INGREDIENT"]
    p_rows = [r for r in rows if r["layer"] == "PARAMETER"]
    for p, info in profs.items():
        for axis in sorted(info["core"]):
            direct = any(r["to"] == axis and matches(r["scope_t"], p) for r in ing_rows)
            if direct:
                continue
            via = False
            for pr in p_rows:
                if pr["to"] == axis and matches(pr["scope_t"], p):
                    if any(r["to"] == pr["owner"] and matches(r["scope_t"], p) for r in ing_rows):
                        via = True
                        break
            if not via:
                q, sc = nearest(p, profs)
                borrow = ""
                if q:
                    src = [r for r in ing_rows if r["to"] == axis and matches(r["scope_t"], q)]
                    via_p = [pr for pr in p_rows if pr["to"] == axis and matches(pr["scope_t"], q)
                             and any(r["to"] == pr["owner"] and matches(r["scope_t"], q) for r in ing_rows)]
                    n = len(src) + len(via_p)
                    borrow = (f"   B5-1 → {scope_str(q)} (겹침 {sc:.2f}, 성분 {n}개, 확신도 -1)" if n
                              else f"   B5-1 → {scope_str(q)} 에도 없음")
                fails["iv"].append(f"{scope_str(p):<40} {axis}{borrow}")
    return fails, conflicts


def main(want_xlsx=False):
    stack = LR.load_stack()
    profs = profiles(stack["S"])
    rows = components(stack)
    fails, conflicts = check(rows, profs)

    print("=" * 72)
    print("  스코프 대장 — RULES C9")
    print("=" * 72)
    print(f"  성분 {len(rows)}  =  " + " · ".join(
        f"{k} {n}" for k, n in collections.Counter(r['kind'] for r in rows).most_common()))
    print(f"  제형 {len(profs)}: " + " · ".join(scope_str(p) for p in profs))
    dotted = sum(1 for r in rows if r["scope_raw"] in ALIASES and r["scope_raw"] != r["scope"])
    print(f"  옛 표기(점·universal)를 정본으로 바꿔 읽은 성분: {dotted}")
    scope_use = collections.Counter(r["scope"] for r in rows)
    print("  스코프별: " + " · ".join(f"{s} {n}" for s, n in scope_use.most_common()))

    names = {"i": "(i) 없는 스코프", "ii": "(ii) 고아 성분 — 맞는 제형 없음",
             "iii": "(iii) 부호 반대, 좁은 쪽에 why 없음", "iii-ok": "(iii) 부호 반대, why 있음 — 의도된 반전",
             "iv": "(iv) 구멍 — core 축에 재료→L 경로 없음", "v": "(v) 중복 (owner, to, scope)"}
    for key in ("i", "ii", "iii", "iii-ok", "iv", "v"):
        lines = fails.get(key, [])
        mark = "  " if key == "iii-ok" else ("!!" if lines else "ok")
        print(f"\n{mark} {names[key]}: {len(lines)}")
        for ln in lines[:40]:
            print("     " + ln)
        if len(lines) > 40:
            print(f"     … {len(lines) - 40} more")

    # 참고: P.axes 가 빈 P
    A = yaml.safe_load(open(os.path.join(LAYERS, "layerA_parameters.yaml"), encoding="utf-8"))["parameters"]
    withp = {r["owner"] for r in rows if r["layer"] == "PARAMETER"}
    empty = [p["id"] for p in A if p["id"] not in withp]
    print(f"\n  참고  axes 가 빈 P: {len(empty)}  " + " ".join(empty))

    hard = sum(len(fails.get(k, [])) for k in ("i", "ii", "iii", "iv", "v"))
    print("\n" + "=" * 72)
    print(f"  걸린 것 {hard}건" + ("" if hard else " — 불변식 다섯 전부 통과"))
    print("=" * 72)

    if want_xlsx:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active; ws.title = "components"
        ws.append(["layer", "kind", "owner", "to", "direction", "magnitude", "scope", "scope_raw",
                   "matches", "why", "id"])
        for r in rows:
            m = [scope_str(p) for p in profs if matches(r["scope_t"], p)]
            ws.append([r["layer"], r["kind"], r["owner"], r["to"], r["direction"], str(r["magnitude"]),
                       r["scope"], r["scope_raw"], ", ".join(m), r["why"], r["extra"]])
        ws2 = wb.create_sheet("invariants")
        ws2.append(["invariant", "line"])
        for key in ("i", "ii", "iii", "iii-ok", "iv", "v"):
            for ln in fails.get(key, []):
                ws2.append([names[key], ln])
        os.makedirs(os.path.dirname(OUT_XLSX), exist_ok=True)
        wb.save(OUT_XLSX)
        print(f"  썼다: {OUT_XLSX}")
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main(want_xlsx="--xlsx" in sys.argv))
