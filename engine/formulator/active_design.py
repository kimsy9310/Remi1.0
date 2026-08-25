"""
Active experimental design — propose the next few MOST INFORMATIVE recipes to
move a starting recipe toward a target sensory profile, using ontology β priors.

Given only: a start recipe + its (benchmark-relative) sensory, the ingredient
palette, and β priors (ingredient->attribute direction x magnitude), it computes:
  gap_k        = target_k - current_k                      (how far each attribute is)
  recommend_j  = sign( Σ_k gap_k · β_jk )                   (which way to move ingredient j)
  impact_j     = |Σ_k gap_k · β_jk|                         (how much j can help)
and proposes a small DOE that perturbs the highest-impact levers in the
recommended directions (kept ~orthogonal for information).
"""
from __future__ import annotations
import numpy as np
from .structured import prior_vector, MAG

def recommend_directions(start_sensory, target, PRIOR, ing_names):
    """Return per-ingredient recommended move (sign) and impact score."""
    attrs = list(PRIOR.keys())
    gap = {k: target.get(k, 0.0) - start_sensory.get(k, 0.0) for k in attrs}
    score = np.zeros(len(ing_names))
    for k in attrs:
        m = prior_vector(PRIOR[k], ing_names)     # β_.k prior (per-std)
        score += gap[k] * m
    rec = {ing_names[j]: (int(np.sign(score[j])), float(abs(score[j])))
           for j in range(len(ing_names))}
    return gap, rec

def propose_doe(rec, start_recipe, ing_names, n_points=6, step=0.4, top_k=4):
    """Small DOE: vary the top-k impactful levers in recommended directions."""
    ranked = sorted(rec.items(), key=lambda kv: -kv[1][1])
    levers = [(n, s) for n, (s, imp) in ranked if s != 0 and imp > 1e-9][:top_k]
    base = dict(start_recipe)
    pts = []
    # 1) all levers moved together (the model's best single guess)
    p = dict(base)
    for n, s in levers:
        p[n] = base.get(n, 0) * (1 + s*step) if base.get(n, 0) else max(0, s)*(1.0)
    pts.append(("all_levers", p))
    # 2) one-lever-at-a-time (informative: isolates each effect)
    for n, s in levers:
        p = dict(base)
        cur = base.get(n, 0)
        p[n] = cur*(1 + s*step) if cur else (2.0 if s > 0 else 0)
        pts.append((f"only_{n}", p))
    return levers, pts[:n_points]
