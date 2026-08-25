"""Dietary / substitution filters - data-driven from origin/allergen/vegan_ok."""
from __future__ import annotations
from .ontology import Ontology


class DietaryFilter:
    def __init__(self, exclude_origin=None, exclude_allergen=None, require_vegan=False):
        self.exclude_origin = set(exclude_origin or [])
        self.exclude_allergen = set(exclude_allergen or [])
        self.require_vegan = require_vegan

    def allows(self, ing) -> bool:
        if self.require_vegan and ing.vegan_ok is False:
            return False
        if ing.origin in self.exclude_origin:
            return False
        if ing.allergen in self.exclude_allergen:
            return False
        return True

    def apply(self, onto: Ontology, ids: list[str]) -> list[str]:
        return [i for i in ids if i in onto.ingredients and self.allows(onto.ingredients[i])]


def substitutes_for(onto: Ontology, ing_id: str, dietary: DietaryFilter | None = None) -> list[str]:
    ing = onto.ingredients.get(ing_id)
    if not ing:
        return []
    subs = ing.substitutes
    if dietary:
        subs = dietary.apply(onto, subs)
    return subs
