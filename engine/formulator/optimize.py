"""
Generic constrained-BO optimization engine that consumes a Projection.

Generalizes the three ad-hoc numpy dry-runs (sauce / ice-cream / vegan) into ONE
engine. The per-scenario, hand-tuned `true_responses()` of the dry-runs is replaced
by a PriorResponseModel built FROM the projection's scoped effect edges + interactions,
so nothing about a specific formulation is hardcoded.

Pure numpy: GP (RBF + Cholesky), constrained Expected-Improvement (feasibility =
maintain responses within tolerance of the benchmark, per Layer B benchmark-relative
model). scipy/sklearn/BoTorch-free; production target swaps in BoTorch/Ax.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import math
import numpy as np
from .ontology import Ontology
from .projection import Projection

_MAG = {"weak": 1.0, "medium": 2.5, "strong": 5.0, "": 2.0, None: 2.0}
_SIGN = {"increase": 1.0, "decrease": -1.0, "": 1.0, None: 1.0}


# --------------------------------------------------------------------------
@dataclass
class DecisionVar:
    id: str                 # ING.* (or a param-backed component)
    low: float = 0.0
    high: float = 0.20

@dataclass
class MixtureProblem:
    structure_class: str
    decision_vars: list[DecisionVar]
    objective: str                          # id of the decision var to MINIMIZE
    maintain: dict[str, float]              # response_id -> tolerance (band half-width)
    benchmark: dict[str, float]             # decision_var id -> fraction (current recipe)
    water_min: float = 0.30

    @property
    def ids(self): return [d.id for d in self.decision_vars]
    def vec(self, d: dict): return np.array([d.get(i, 0.0) for i in self.ids])


# --------------------------------------------------------------------------
class PriorResponseModel:
    """Synthetic ground-truth built from ontology priors (cold-start simulator).
    response(x) = base + Σ effects(sign*mag*fraction) + Σ synergy(product), computed
    for each maintained response via edges targeting the response OR its proxy params."""
    def __init__(self, onto: Ontology, proj: Projection, problem: MixtureProblem, noise=0.25, seed=7):
        self.o, self.proj, self.p = onto, proj, problem
        self.noise = noise
        self.rng = np.random.default_rng(seed)
        self.resp_ids = list(problem.maintain.keys())
        # map response -> set of targets it responds to (itself + instrumental proxies)
        self.targets = {}
        for r in self.resp_ids:
            ts = {r}
            for resp in proj.responses:
                if resp["id"] == r:
                    ts.update(resp.get("instrumental_proxy") or [])
            self.targets[r] = ts
        # precompute per-response linear weights over decision vars, + synergy terms
        self.W = {r: self._weights_for(r) for r in self.resp_ids}
        self.syn = self._synergies()

    def _tags_of(self, ing_id):
        ing = self.o.ingredients.get(ing_id)
        return set(ing.function_tags) if ing else set()

    def _weights_for(self, response_id):
        tgt = self.targets[response_id]
        w = np.zeros(len(self.p.ids))
        for j, vid in enumerate(self.p.ids):
            vtags = self._tags_of(vid)
            for e in self.proj.priors:
                if e.get("to") not in tgt:
                    continue
                frm, kind = e["_from"], e["_kind"]
                hit = (kind == "ingredient" and frm == vid) or (kind == "tag" and frm in vtags)
                if hit:
                    w[j] += _SIGN.get(e.get("direction")) * _MAG.get(e.get("magnitude"))
        return w

    def _synergies(self):
        out = []
        for ix in self.proj.interactions:
            members = ix.get("between", [])
            idx = [self.p.ids.index(m) for m in members if m in self.p.ids]
            if len(idx) >= 2:
                sign = 1.0 if ix.get("type") == "synergy" else -1.0
                out.append((idx, sign, ix.get("on_target")))
        return out

    def _raw(self, x):
        out = {}
        for r in self.resp_ids:
            val = 5.0 + float(self.W[r] @ (x * 20.0))       # scale fractions to ~0-15 band
            for idx, sign, tgt in self.syn:
                if tgt in self.targets[r] or (tgt is None):
                    prod = np.prod([x[i] for i in idx]) * 400.0
                    val += sign * prod
            out[r] = val
        return out

    def measure(self, x, noisy=True):
        r = self._raw(np.asarray(x, float))
        if noisy:
            for k in r: r[k] += self.rng.normal(0, self.noise)
        return r


# --------------------------------------------------------------------------
class GP:
    def __init__(self, lo, hi, l=0.35, sf=1.0, noise=0.08):
        self.lo, self.hi = lo, hi; self.l, self.sf, self.noise = l, sf, noise
    def _n(self, X): return (X - self.lo) / np.where(self.hi - self.lo == 0, 1, self.hi - self.lo)
    def _k(self, A, B):
        d = ((A[:, None, :] - B[None, :, :]) ** 2).sum(-1)
        return self.sf ** 2 * np.exp(-0.5 * d / self.l ** 2)
    def fit(self, X, y):
        self.X = self._n(X); self.ym = y.mean(); self.ys = y.std() + 1e-9
        yc = (y - self.ym) / self.ys
        K = self._k(self.X, self.X) + self.noise ** 2 * np.eye(len(X))
        self.L = np.linalg.cholesky(K)
        self.al = np.linalg.solve(self.L.T, np.linalg.solve(self.L, yc)); return self
    def predict(self, Xs):
        Xn = self._n(Xs); Ks = self._k(Xn, self.X)
        mu = Ks @ self.al * self.ys + self.ym
        v = np.linalg.solve(self.L, Ks.T)
        var = (self.sf ** 2 - (v ** 2).sum(0)) * self.ys ** 2
        return mu, np.clip(var, 1e-9, None)

_Phi = lambda z: 0.5 * (1 + np.vectorize(math.erf)(z / math.sqrt(2)))
def _p_within(mu, sd, center, tol):
    return _Phi((center + tol - mu) / sd) - _Phi((center - tol - mu) / sd)


# --------------------------------------------------------------------------
@dataclass
class OptResult:
    best_x: dict
    objective_start: float
    objective_best: float
    reduction_pct: float
    responses_true: dict
    feasible: bool
    n_eval: int
    trace: list = field(default_factory=list)


def optimize(problem: MixtureProblem, model: PriorResponseModel,
             n_init=8, n_iter=30, pool=4000, seed=7) -> OptResult:
    rng = np.random.default_rng(seed)
    ids = problem.ids
    lo = np.array([d.low for d in problem.decision_vars])
    hi = np.array([d.high for d in problem.decision_vars])
    obj_j = ids.index(problem.objective)
    resp_ids = list(problem.maintain.keys())
    tol = np.array([problem.maintain[r] for r in resp_ids])
    xb = problem.vec(problem.benchmark)
    rb = model.measure(xb, noisy=False)
    rb_v = np.array([rb[r] for r in resp_ids])

    def sample(n, near=None):
        out = []
        while len(out) < n:
            if near is not None:
                x = near * rng.uniform(0.6, 1.05, size=len(ids))
                x = np.clip(x, lo, hi)
            else:
                x = lo + rng.uniform(size=len(ids)) * (hi - lo)
            if 1 - x.sum() >= problem.water_min:
                out.append(x)
        return np.array(out)

    def measure_arr(X):
        M = []
        for x in X:
            r = model.measure(x, noisy=True)
            M.append([r[k] for k in resp_ids])
        return np.array(M)

    def feas(M):
        return np.all(np.abs(M - rb_v) <= tol, axis=1)

    X = sample(max(n_init-1, 4)); X = np.vstack([xb, X]); Y = measure_arr(X)
    trace = []
    for _ in range(n_iter):
        f = feas(Y)
        best = X[f, obj_j].min() if f.any() else np.nan
        trace.append(best)
        gps = [GP(lo, hi).fit(X, Y[:, k]) for k in range(len(resp_ids))]
        C = sample(pool)
        mus = []; pf = np.ones(len(C))
        for k, gp in enumerate(gps):
            mu, var = gp.predict(C); mus.append(mu)
            pf *= _p_within(mu, np.sqrt(var), rb_v[k], tol[k])
        if not f.any():
            acq = pf
        else:
            improvement = np.clip(best - C[:, obj_j], 0, None)
            acq = improvement * pf + 0.01 * np.sqrt(sum(gp.predict(C)[1] for gp in gps))
        xn = C[np.argmax(acq)]
        X = np.vstack([X, xn]); Y = np.vstack([Y, measure_arr(xn[None])])

    f = feas(Y)
    if f.any():
        bi = np.where(f)[0][np.argmin(X[f, obj_j])]
    else:
        bi = int(np.argmin(np.abs(Y - rb_v).sum(1)))
    xbest = X[bi]
    rt = model.measure(xbest, noisy=False)
    start = xb[obj_j]; best = xbest[obj_j]
    trace.append(X[f, obj_j].min() if f.any() else best)
    return OptResult(
        best_x={i: round(float(v), 4) for i, v in zip(ids, xbest)},
        objective_start=round(float(start), 4), objective_best=round(float(best), 4),
        reduction_pct=round((1 - best / start) * 100, 1) if start > 0 else 0.0,
        responses_true={k: round(float(rt[k]), 2) for k in resp_ids},
        feasible=bool(f.any()), n_eval=len(X), trace=[float(t) for t in trace])
