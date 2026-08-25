"""
Substitution advisor — recommends REPLACING an ingredient when its downside on a
'defect' attribute is too strong AND a functional twin (same role) exists with a
smaller downside but comparable benefits. Discrete rule layer on top of the
continuous optimizer. Powered by ontology: function group + effect vector + substitutes.
"""
from __future__ import annotations
import numpy as np

def recommend_substitutions(recipe, beta, groups, defect_attrs, benefit_attrs,
                            ingredient_amounts=None, min_gain=0.8):
    """
    recipe          : {ingredient: amount}
    beta            : {attribute: {ingredient: per-unit effect (signed magnitude 0..3)}}
    groups          : {ingredient: functional_group}   (twins share a group)
    defect_attrs    : list of attributes where LOWER is better (e.g. 'oxidated oil')
    benefit_attrs   : list of attributes the ingredient is kept FOR (e.g. 'mouthfeel')
    Returns ranked list of {from, to, defect, defect_drop, benefit_kept, reason}.
    """
    recs = []
    present = [i for i, a in recipe.items() if a and a > 0]
    for ing in present:
        grp = groups.get(ing)
        if grp is None:
            continue
        # how bad is this ingredient on defect attributes (per-unit)?
        defect_load = {d: beta.get(d, {}).get(ing, 0) for d in defect_attrs}
        worst_d = max(defect_attrs, key=lambda d: defect_load[d], default=None)
        if worst_d is None or defect_load[worst_d] < 1:      # not a strong defect driver
            continue
        # candidate twins: same group, present-or-available, lower defect load
        twins = [t for t, g in groups.items() if g == grp and t != ing]
        best = None
        for t in twins:
            d_new = beta.get(worst_d, {}).get(t, 0)
            gain = defect_load[worst_d] - d_new              # defect reduction per unit
            # benefits preserved? twin should match on the benefit axes
            ben_ing = np.array([beta.get(b, {}).get(ing, 0) for b in benefit_attrs])
            ben_twin = np.array([beta.get(b, {}).get(t, 0) for b in benefit_attrs])
            keeps = np.all(ben_twin >= ben_ing - 0.5)        # twin does the job ~as well
            if gain >= min_gain and keeps:
                if best is None or gain > best[1]:
                    best = (t, gain, d_new, ben_twin)
        if best:
            t, gain, d_new, ben_twin = best
            recs.append({
                "from": ing, "to": t, "defect": worst_d,
                "defect_per_unit": f"{defect_load[worst_d]:.0f} -> {d_new:.0f}",
                "benefit_kept": {b: float(beta.get(b, {}).get(t, 0)) for b in benefit_attrs},
                "reason": (f"'{ing}' is the main driver of '{worst_d}' "
                           f"(effect {defect_load[worst_d]:.0f}); functional twin '{t}' "
                           f"gives the same {benefit_attrs} role with far less '{worst_d}' "
                           f"(effect {d_new:.0f}). Recommend SWAP, not increase.")
            })
    return sorted(recs, key=lambda r: -float(r["defect_per_unit"].split("->")[0]))


# --------------------------------------------------------------------------
# Ontology-driven tiered advisor (reads defect_cause_map + descriptors)
_LEVEL = {"low": 0, "medium": 1, "high": 2, None: 1}

def advise_from_ontology(onto, offender_id, defect_id, palette_ids):
    """Tier 1 (palette swap) / Tier 2 (library add) / Tier 3 (spec + mitigation)."""
    dc = onto.defect_cause.get(defect_id)
    if not dc:
        return {"tier": 0, "msg": f"no defect_cause entry for {defect_id}"}
    desc = dc["driver_descriptor"]; bad_when = dc.get("bad_when", "low")
    off = onto.ingredients.get(offender_id)
    if not off:
        return {"tier": 0, "msg": f"unknown ingredient {offender_id}"}
    off_tags = set(off.function_tags)
    def lvl(x):
        return _LEVEL.get(str(x).lower()) if str(x).lower() in _LEVEL else None
    off_level = lvl(off.descriptors.get(desc))
    if off_level is None:
        return {"tier": 0, "msg": f"{offender_id} has no '{desc}' descriptor to reason on"}

    def is_good_twin(ing):
        if ing.id == offender_id or not (off_tags & set(ing.function_tags)):
            return False                       # must share a functional role
        lv = lvl(ing.descriptors.get(desc))
        if lv is None:
            return False                       # unknown property -> cannot confirm it is better
        return (lv > off_level) if bad_when == "low" else (lv < off_level)

    twins = [i.id for i in onto.ingredients.values() if is_good_twin(i)]
    in_palette = [t for t in twins if t in palette_ids]
    in_library = [t for t in twins if t not in palette_ids]
    base = {"offender": offender_id, "defect": defect_id,
            "descriptor": desc, "bad_when": bad_when, "mechanism": dc.get("mechanism")}
    if in_palette:
        return {**base, "tier": 1, "action": "SWAP within your ingredients", "options": in_palette}
    if in_library:
        return {**base, "tier": 2, "action": "ADD from ontology library", "options": in_library}
    return {**base, "tier": 3, "action": "no twin anywhere -> spec + mitigation",
            "spec": dc.get("ideal_substitute_spec"), "mitigations": dc.get("mitigations", [])}
