"""
Projection: ontology + goal spec  ->  optimizer-ready problem.
Fully generic: reads whatever structure class / tags / effects exist.

A GoalSpec names, per response (SA.* or P.*):  target | maintain | minimize | maximize.
Unspecified relevant_attributes default to their ontology default_goal.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from .ontology import Ontology
from .filters import DietaryFilter


@dataclass
class Projection:
    structure_class: str
    decision_variables: list[dict] = field(default_factory=list)  # candidate ingredient palette
    responses: list[dict] = field(default_factory=list)           # SA/P + goal + proxies
    constraints: list[dict] = field(default_factory=list)         # hard guards / limits
    priors: list[dict] = field(default_factory=list)              # scoped effect edges
    interactions: list[dict] = field(default_factory=list)

    def summary(self) -> str:
        L = [f"PROJECTION  <{self.structure_class}>",
             f"  decision vars (palette): {len(self.decision_variables)}",
             f"  responses:               {len(self.responses)}",
             f"  constraints:             {len(self.constraints)}",
             f"  priors (scoped effects): {len(self.priors)}",
             f"  interactions:            {len(self.interactions)}"]
        return "\n".join(L)


def project(onto: Ontology, structure_class: str, goals: dict | None = None,
            dietary: DietaryFilter | None = None) -> Projection:
    goals = goals or {}
    if structure_class not in onto.structure_classes:
        raise KeyError(f"unknown structure class {structure_class!r}")
    sc = onto.structure_classes[structure_class]
    p = Projection(structure_class=structure_class)

    # ---- priors: all effect edges scoped to this class ----
    scoped_effects = onto.effects_scoped_to(structure_class)
    p.priors = scoped_effects

    # tags that actually act in this class -> the RELEVANT function tags here
    active_tags = {e["_from"] for e in scoped_effects if e["_kind"] == "tag"}
    # ingredients that carry an active tag, OR have an override/flavor edge scoped here
    palette = set()
    for iid, ing in onto.ingredients.items():
        if active_tags.intersection(ing.function_tags):
            palette.add(iid)
        if any(_scoped(e, structure_class) for e in ing.overrides + ing.flavor_profile):
            palette.add(iid)
    palette = sorted(palette)
    if dietary:
        palette = dietary.apply(onto, palette)
    for iid in palette:
        ing = onto.ingredients[iid]
        p.decision_variables.append({
            "id": iid, "label": ing.label, "tags": ing.function_tags,
            "descriptors": ing.descriptors, "origin": ing.origin,
            "limitations": ing.limitations})

    # ---- responses: relevant_attributes of the class (+ goal override) ----
    for ra in sc.relevant_attributes:
        aid = ra.get("id")
        goal = goals.get(aid) or ra.get("default_goal") or _default_goal(onto, aid)
        proxies = _proxies_for(onto, aid, structure_class)
        p.responses.append({"id": aid, "goal": goal,
                            "modality": ra.get("modality", ""),
                            "instrumental_proxy": proxies,
                            "driver_layer": ra.get("driver_layer")})

    # ---- constraints: ingredient upper limits (in palette) + plausible_range + typical_constraints ----
    for iid in palette:
        for lim in onto.ingredients[iid].limitations:
            if isinstance(lim, dict) and _scoped(lim, structure_class):
                p.constraints.append({"kind": "ingredient_limit", "ingredient": iid, **lim})
    for pid in sc.params:
        pr = onto.params[pid].plausible_range
        if pr is not None:
            p.constraints.append({"kind": "plausible_range", "param": pid, "range": pr})
    for c in sc.constraints:
        p.constraints.append({"kind": "typical_constraint", **(_asdict(c))})

    # ---- interactions scoped to this class ----
    for ix in onto.interactions:
        if _scoped(ix, structure_class):
            p.interactions.append(ix)

    return p


def apply_reformulation_pattern(onto: Ontology, pattern_id: str):
    """Return (structure_class, dietary, compensation ingredients) for a named pattern."""
    rp = onto.reformulation_patterns.get(pattern_id)
    if not rp:
        raise KeyError(pattern_id)
    excl = rp.get("exclude_origin")
    dietary = DietaryFilter(exclude_origin=excl) if excl else None
    return rp.get("structure_class"), dietary, rp.get("compensation", [])


# ---- helpers ----
def _scoped(e, scid):
    s = e.get("scoped_to_structure_class")
    return s == scid or s == "any" or (isinstance(s, list) and (scid in s or "any" in s))

def _default_goal(onto, aid):
    a = onto.sensory.get(aid)
    return (a.default_goal if a else "") or "maintain"

def _proxies_for(onto, aid, scid):
    a = onto.sensory.get(aid)
    if not a:
        return []
    # global proxy or per-class calibration proxy
    if a.data.get("instrumental_proxy"):
        return a.data["instrumental_proxy"]
    for ap in a.applies_to:
        if isinstance(ap, dict) and ap.get("structure_class") == scid:
            return ap.get("instrumental_proxy", [])
    return []

def _asdict(c):
    return c if isinstance(c, dict) else {"statement": c}
