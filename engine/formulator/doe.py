"""
Fine-tuning DoE generator. Given a CONFIRMED base recipe and a few ACTIVE levers
(ingredients being added/changed), propose a small, efficient set of experiments
that map how those levers move the target attributes — minimal runs, informative.

Design = center point + 2-level factorial corners (full if <=3 levers, else half
fraction) + optional axial/star points (for curvature). Water (filler) is
auto-balanced so the batch total stays constant.
"""
from __future__ import annotations
import itertools
import numpy as np

def _balance(recipe, filler, total):
    if filler in recipe:
        others = sum(v for k, v in recipe.items() if k != filler)
        recipe[filler] = round(max(0.0, total - others), 3)
    return recipe

def design_experiments(base, levers, style="ccf", filler="water"):
    """base: {ingredient: amount}; levers: {ingredient: (low, high)}.
    style: 'factorial' (center+corners) or 'ccf' (+ axial star points)."""
    base = dict(base); keys = list(levers); k = len(keys)
    total = sum(base.values())
    los = [levers[x][0] for x in keys]; his = [levers[x][1] for x in keys]
    mids = [(l + h) / 2 for l, h in zip(los, his)]
    pts = [("center", tuple(mids))]
    corners = list(itertools.product(*[(l, h) for l, h in zip(los, his)]))
    if k > 3:  # half fraction: keep corners whose product of signs = +1
        def sign(v, i): return 1 if v == his[i] else -1
        corners = [c for c in corners if np.prod([sign(c[i], i) for i in range(k)]) > 0]
    pts += [("corner", c) for c in corners]
    if style == "ccf":
        for i in range(k):
            for lv in (los[i], his[i]):
                p = list(mids); p[i] = lv; pts.append(("axial", tuple(p)))
    # build + dedup
    seen = set(); runs = []
    for tag, vals in pts:
        key = tuple(round(v, 4) for v in vals)
        if key in seen: continue
        seen.add(key)
        r = dict(base)
        for i, ing in enumerate(keys): r[ing] = round(vals[i], 3)
        _balance(r, filler, total)
        runs.append((tag, r))
    return keys, runs

def annotate(pred, names, runs, target_attrs):
    """Predicted sensory (for the target attributes) of each run, via the current model."""
    out = []
    for tag, r in runs:
        x = np.array([r.get(n, 0.0) for n in names])
        s = pred.predict(x)
        out.append((tag, r, {a: round(float(s[pred.snames.index(a)]), 2) for a in target_attrs}))
    return out


def expand_premixes(recipe, premixes):
    """Replace a premix pseudo-ingredient by its fixed-ratio components.
    premixes: {premix_name: {component: fraction}}. The premix stays fixed-ratio;
    only its TOTAL amount (a design variable) changes. Not an ontology ingredient."""
    out = {}
    for k, amt in recipe.items():
        if k in premixes:
            for comp, frac in premixes[k].items():
                out[comp] = round(out.get(comp, 0.0) + amt * frac, 4)
        else:
            out[k] = round(out.get(k, 0.0) + amt, 4)
    return out
