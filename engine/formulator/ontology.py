"""
Ontology loader -> unified in-memory property graph.

Design guard (from roadmap): GENERIC / ontology-driven. Nothing about specific
structure classes (sauce/beverage/ice_cream) is hardcoded. Adding a new formulation
class or ingredient = adding YAML, never editing this engine.

Merges base + all *_ext files (union), applies tag_additions, ingredient overrides,
and origin annotations. Builds typed nodes and edges.
"""
from __future__ import annotations
import glob, os
from dataclasses import dataclass, field
from typing import Any
import yaml


# ----------------------------- node containers -----------------------------
@dataclass
class StructureClass:
    id: str
    label: str = ""
    axes: dict = field(default_factory=dict)
    params: list[str] = field(default_factory=list)          # P.* ids
    cross_links: list[dict] = field(default_factory=list)    # {from,to,direction,...}
    relevant_attributes: list[dict] = field(default_factory=list)  # {id: SA.*, default_goal,...}
    constraints: list[dict] = field(default_factory=list)    # typical_constraints
    raw: dict = field(default_factory=dict)

@dataclass
class Param:
    id: str
    data: dict = field(default_factory=dict)
    structure_class: str | None = None
    plausible_range: Any = None

@dataclass
class SensoryAttribute:
    id: str
    modality: str = ""
    default_goal: str = ""
    applies_to: list[dict] = field(default_factory=list)     # per-class calibration + proxies
    driver_layer: str | None = None
    data: dict = field(default_factory=dict)

@dataclass
class FunctionTag:
    id: str
    label: str = ""
    effects: list[dict] = field(default_factory=list)        # scoped effect edges
    specializes: str | None = None
    generalizes: str | None = None
    data: dict = field(default_factory=dict)

@dataclass
class Ingredient:
    id: str
    label: str = ""
    function_tags: list[str] = field(default_factory=list)
    descriptors: dict = field(default_factory=dict)
    origin: str | None = None
    allergen: str | None = None
    vegan_ok: Any = None
    limitations: list = field(default_factory=list)
    substitutes: list[str] = field(default_factory=list)
    overrides: list[dict] = field(default_factory=list)      # ingredient-level effect overrides
    flavor_profile: list[dict] = field(default_factory=list) # contribution edges to SA.flavor.*
    external_ref: dict = field(default_factory=dict)


class Ontology:
    def __init__(self):
        self.structure_classes: dict[str, StructureClass] = {}
        self.params: dict[str, Param] = {}
        self.sensory: dict[str, SensoryAttribute] = {}
        self.tags: dict[str, FunctionTag] = {}
        self.ingredients: dict[str, Ingredient] = {}
        self.interactions: list[dict] = []
        self.reformulation_patterns: dict[str, dict] = {}
        self.defect_cause: dict[str, dict] = {}

    # ---- loading ----
    @classmethod
    def load(cls, path: str) -> "Ontology":
        o = cls()
        docs = []
        for f in sorted(glob.glob(os.path.join(path, "*.yaml"))):
            with open(f, encoding="utf-8") as fh:
                d = yaml.safe_load(fh)
            if d:
                docs.append((os.path.basename(f), d))
        for name, d in docs:
            o._ingest(name, d)
        o._post_merge()
        return o

    def _ingest(self, name: str, d: dict):
        # Layer A structure classes
        if "structure_class" in d:
            sc = d["structure_class"]
            scid = sc["id"]
            obj = StructureClass(
                id=scid, label=sc.get("label", ""), axes=sc.get("axes", {}),
                cross_links=sc.get("cross_links", []),
                relevant_attributes=sc.get("relevant_attributes", []),
                constraints=sc.get("typical_constraints", []), raw=sc)
            for p in sc.get("parameters", []):
                pid = p["id"]
                obj.params.append(pid)
                self.params[pid] = Param(id=pid, data=p, structure_class=scid,
                                         plausible_range=p.get("plausible_range"))
            self.structure_classes[scid] = obj

        # Layer B sensory attributes (base + ext + flavor)
        for key in ("sensory_attributes", "sensory_attributes_ext", "flavor_attributes", "flavor_vocabulary"):
            for a in _as_list(d.get(key)):
                if not isinstance(a, dict) or "id" not in a:
                    continue
                aid = a["id"]
                self.sensory[aid] = SensoryAttribute(
                    id=aid, modality=a.get("modality", ""),
                    default_goal=a.get("default_goal", ""),
                    applies_to=_as_list(a.get("applies_to")),
                    driver_layer=a.get("driver_layer"), data=a)

        # Layer C function tags (base + ext) - UNION by id, merge effects
        for key in ("function_tags", "function_tags_ext"):
            for t in _as_list(d.get(key)):
                if not isinstance(t, dict) or "id" not in t:
                    continue
                tid = t["id"]
                ft = self.tags.get(tid) or FunctionTag(id=tid)
                ft.label = ft.label or t.get("label", "")
                ft.effects += t.get("effects", [])
                ft.specializes = ft.specializes or t.get("specializes")
                ft.generalizes = ft.generalizes or t.get("generalizes")
                ft.data = {**ft.data, **t}
                self.tags[tid] = ft

        # Layer C ingredients (base + ext) - UNION by id
        for key in ("ingredients", "ingredients_ext"):
            for ing in _as_list(d.get(key)):
                if not isinstance(ing, dict) or "id" not in ing:
                    continue
                iid = ing["id"]
                obj = self.ingredients.get(iid) or Ingredient(id=iid)
                obj.label = obj.label or ing.get("label", "")
                obj.function_tags = _union(obj.function_tags, ing.get("function_tags", []))
                obj.descriptors = {**obj.descriptors, **ing.get("descriptors", {})}
                for fld in ("origin", "allergen", "vegan_ok"):
                    if ing.get(fld) is not None:
                        setattr(obj, fld, ing[fld])
                obj.limitations += ing.get("limitations", [])
                obj.substitutes = _union(obj.substitutes, ing.get("substitutes", []))
                obj.overrides += ing.get("overrides", [])
                obj.flavor_profile += ing.get("flavor_profile", [])
                if ing.get("external_ref"):
                    obj.external_ref = {**obj.external_ref, **_as_ref(ing["external_ref"])}
                self.ingredients[iid] = obj

        # additive tag re-tagging (stabilizer ext)
        for ta in _as_list(d.get("tag_additions")):
            iid = ta.get("ingredient")
            if iid and iid in self.ingredients:
                self.ingredients[iid].function_tags = _union(
                    self.ingredients[iid].function_tags, ta.get("add_tags", []))

        # origin annotations (vegan_gaps audit block) - idempotent merge
        for oa in _as_list(d.get("origin_annotations")):
            iid = oa.get("ingredient")
            if iid and iid in self.ingredients:
                ing = self.ingredients[iid]
                for fld in ("origin", "allergen", "vegan_ok"):
                    if oa.get(fld) is not None and getattr(ing, fld) is None:
                        setattr(ing, fld, oa[fld])

        # interactions + reformulation patterns
        self.interactions += _as_list(d.get("interactions"))
        for rp in _as_list(d.get("reformulation_patterns")):
            if isinstance(rp, dict) and "id" in rp:
                self.reformulation_patterns[rp["id"]] = rp
        for dc in _as_list(d.get("defect_cause_map")):
            if isinstance(dc, dict) and "defect" in dc:
                self.defect_cause[dc["defect"]] = dc

    def _post_merge(self):
        # pre-index effects (tag + ingredient overrides) by (target, structure_class)
        self.effect_index: list[dict] = []
        for t in self.tags.values():
            for e in t.effects:
                self.effect_index.append({**e, "_from": t.id, "_kind": "tag"})
        for ing in self.ingredients.values():
            for e in ing.overrides:
                self.effect_index.append({**e, "_from": ing.id, "_kind": "ingredient"})

    # ---- convenience queries ----
    def ingredients_with_tag(self, tag: str) -> list[str]:
        return [i.id for i in self.ingredients.values() if tag in i.function_tags]

    def effects_scoped_to(self, scid: str) -> list[dict]:
        out = []
        for e in self.effect_index:
            s = e.get("scoped_to_structure_class")
            if s == scid or s == "any" or (isinstance(s, list) and (scid in s or "any" in s)):
                out.append(e)
        return out


# ----------------------------- helpers -----------------------------
def _as_list(x):
    if x is None: return []
    return x if isinstance(x, list) else [x]

def _union(a, b):
    out = list(a)
    for x in _as_list(b):
        if x not in out: out.append(x)
    return out

def _as_ref(x):
    return x if isinstance(x, dict) else {"ref": x}
