"""Export the property graph to Neo4j Cypher CREATE statements.
This is the 'projection -> Cypher / property graph' systematization step:
the same in-memory ontology can be materialized in Neo4j without changing the engine.
"""
from __future__ import annotations
from .ontology import Ontology


def _s(v):
    return str(v).replace("\\", "\\\\").replace("'", "\\'")

def export(onto: Ontology) -> str:
    lines = ["// ---- NODES ----"]
    for sc in onto.structure_classes.values():
        lines.append(f"CREATE (:StructureClass {{id:'{_s(sc.id)}', label:'{_s(sc.label)}'}});")
    for pid, p in onto.params.items():
        lines.append(f"CREATE (:Param {{id:'{_s(pid)}', structure_class:'{_s(p.structure_class)}'}});")
    for a in onto.sensory.values():
        lines.append(f"CREATE (:SensoryAttribute {{id:'{_s(a.id)}', modality:'{_s(a.modality)}', default_goal:'{_s(a.default_goal)}'}});")
    for t in onto.tags.values():
        lines.append(f"CREATE (:FunctionTag {{id:'{_s(t.id)}', label:'{_s(t.label)}'}});")
    for ing in onto.ingredients.values():
        lines.append(f"CREATE (:Ingredient {{id:'{_s(ing.id)}', label:'{_s(ing.label)}', origin:'{_s(ing.origin)}', vegan_ok:'{_s(ing.vegan_ok)}'}});")

    lines.append("// ---- RELATIONSHIPS ----")
    # structure_class HAS_PARAM param
    for sc in onto.structure_classes.values():
        for pid in sc.params:
            lines.append(_rel("StructureClass", sc.id, "HAS_PARAM", "Param", pid))
        for ra in sc.relevant_attributes:
            if ra.get("id"):
                lines.append(_rel("StructureClass", sc.id, "RELEVANT_ATTRIBUTE", "SensoryAttribute", ra["id"],
                                  {"default_goal": ra.get("default_goal", "")}))
    # ingredient HAS_TAG tag ; ingredient SUBSTITUTE ingredient
    for ing in onto.ingredients.values():
        for t in ing.function_tags:
            lines.append(_rel("Ingredient", ing.id, "HAS_TAG", "FunctionTag", t))
        for s in ing.substitutes:
            lines.append(_rel("Ingredient", ing.id, "SUBSTITUTE", "Ingredient", s))
    # scoped EFFECT edges (tag/ingredient -> param/attribute)
    for e in onto.effect_index:
        tgt = e.get("to")
        if not tgt:
            continue
        tlabel = "Param" if str(tgt).startswith("P.") else "SensoryAttribute"
        src_label = "FunctionTag" if e["_kind"] == "tag" else "Ingredient"
        props = {"direction": e.get("direction", ""), "magnitude": e.get("magnitude", ""),
                 "scope": _scope_str(e.get("scoped_to_structure_class")),
                 "source_type": e.get("source_type", "")}
        lines.append(_rel(src_label, e["_from"], "EFFECT", tlabel, tgt, props))
    return "\n".join(lines) + "\n"

def _scope_str(s):
    if isinstance(s, list): return "|".join(s)
    return str(s)

def _rel(la, ida, rel, lb, idb, props=None):
    p = ""
    if props:
        p = " {" + ", ".join(f"{k}:'{_s(v)}'" for k, v in props.items()) + "}"
    return (f"MATCH (a:{la} {{id:'{_s(ida)}'}}),(b:{lb} {{id:'{_s(idb)}'}}) "
            f"CREATE (a)-[:{rel}{p}]->(b);")
