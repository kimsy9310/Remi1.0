"""
Ontology-STRUCTURED Bayesian predictor (gray-box) — the prior->learned model.

y_k(recipe) = mean_k + Σ_{j in scope(k)} β_jk · z(x_j)      (+ nonlinearity/interactions later)

  - scope(k)  : only ontology-relevant ingredients feed attribute k
  - β_jk prior: ontology DIRECTION x MAGNITUDE (per-std units)   <-- the "vector"
  - fit       : ridge-TO-PRIOR  β = (ZᵀZ + λI)⁻¹(Zᵀy + λ·m)
                λ large  -> β≈prior (data silent -> keep knowledge)
                λ small  -> β≈data  (data rich  -> refine)
Pure numpy. z() = per-column standardization.
"""
from __future__ import annotations
import numpy as np

# magnitude {0,1,2,3} -> effect per 1 std of the ingredient, on the -3..+3 scale
MAG = {0: 0.0, 1: 0.3, 2: 0.6, 3: 1.0}
# per-edge confidence -> prior precision (Λ). high = trust prior (strong pull);
# low = hypothesis (data easily overrides). "medium" is the default.
CONF = {"high": 8.0, "medium": 2.0, "low": 0.4, None: 2.0}

def prior_and_conf(prior_row, ing_names, default_conf="medium"):
    """prior_row values may be int (magnitude) or (magnitude, conf_label)."""
    import numpy as _np
    m = _np.zeros(len(ing_names)); lam = _np.zeros(len(ing_names))
    for j, n in enumerate(ing_names):
        e = prior_row.get(n)
        if e is None:
            m[j] = 0.0; lam[j] = CONF["low"]          # unmentioned -> weak zero-prior
            continue
        if isinstance(e, (tuple, list)):
            val, conf = e[0], e[1]
        else:
            val, conf = e, default_conf
        m[j] = _np.sign(val) * MAG[abs(int(val))]; lam[j] = CONF.get(conf, 2.0)
    return m, lam

def prior_vector(prior_row, ing_names):
    """prior_row: {ingredient_name: signed_magnitude(-3..3)} -> m aligned to ing_names."""
    m = np.zeros(len(ing_names))
    for j, n in enumerate(ing_names):
        v = prior_row.get(n, 0)
        m[j] = np.sign(v) * MAG[abs(int(v))]
    return m

class StructuredModel:
    def __init__(self, lam=1.0):
        self.lam = lam
    def fit(self, X, y, m, scope_idx, lam_vec=None, mu=None, sd=None):
        self.scope = scope_idx
        Xs = X[:, scope_idx]
        if mu is None:
            mu = Xs.mean(0); sd = Xs.std(0)
        self.mu = mu; self.sd = np.where(np.asarray(sd) < 1e-9, 1.0, sd)
        Z = (Xs - self.mu) / self.sd
        self.ym = y.mean(); yc = y - self.ym
        ms = m[scope_idx]
        if lam_vec is None:
            Lam = self.lam * np.eye(Z.shape[1])
        else:
            Lam = np.diag(np.asarray(lam_vec)[scope_idx])   # per-edge precision
        A = Z.T @ Z + Lam
        self.beta = np.linalg.solve(A, Z.T @ yc + Lam @ ms)
        self.prior = ms
        return self
    def predict(self, X):
        Z = (X[:, self.scope] - self.mu) / self.sd
        return Z @ self.beta + self.ym

def loo_structured(X, y, m, scope_idx, lam=1.0):
    n = len(y); pred = np.zeros(n)
    Xs = X[:, scope_idx]                         # GLOBAL standardization (robust to LOO)
    gmu = Xs.mean(0); gsd = Xs.std(0)
    for i in range(n):
        tr = [k for k in range(n) if k != i]
        mdl = StructuredModel(lam).fit(X[tr], y[tr], m, scope_idx, mu=gmu, sd=gsd)
        pred[i] = mdl.predict(X[i:i+1])[0]
    rmse = np.sqrt(np.mean((pred - y) ** 2))
    r = np.corrcoef(pred, y)[0, 1] if y.std() > 1e-9 and pred.std() > 1e-9 else np.nan
    return rmse, r, pred


# --------------------------------------------------------------------------
# MULTI-TASK structured model: ontology prior M0 (sparse, per-attribute scope)
# + a LOW-RANK data correction SHARED across attributes (borrows strength /
# absorbs attribute-attribute correlation). rank=0 -> prior only.
class MultiTaskStructured:
    def __init__(self, rank=1, lam=1.0):
        self.rank = rank; self.lam = lam
    def fit(self, X, Y, M0, feat_idx, mu, sd):
        self.feat = feat_idx; self.mu = mu; self.sd = sd
        Z = (X[:, feat_idx] - mu) / sd
        self.ym = Y.mean(0); Yc = Y - self.ym
        R = Yc - Z @ M0                                   # residual after ontology prior
        Brr = np.zeros_like(M0)
        if self.rank > 0:
            A = Z.T @ Z + self.lam * np.eye(Z.shape[1])
            Bols = np.linalg.solve(A, Z.T @ R)            # ridge OLS on residual
            Fit = Z @ Bols
            U, S, Vt = np.linalg.svd(Fit, full_matrices=False)
            r = min(self.rank, Vt.shape[0])
            Vr = Vt[:r].T
            Brr = Bols @ Vr @ Vr.T                        # rank-r shared correction
        self.B = M0 + Brr
        return self
    def predict(self, X):
        Z = (X[:, self.feat] - self.mu) / self.sd
        return Z @ self.B + self.ym

def loo_multitask(X, Y, M0, feat_idx, rank=1, lam=1.0):
    n, m = Y.shape; pred = np.zeros_like(Y)
    Zf = X[:, feat_idx]; mu = Zf.mean(0); sd = Zf.std(0); sd[sd < 1e-9] = 1.0
    for i in range(n):
        tr = [k for k in range(n) if k != i]
        mdl = MultiTaskStructured(rank, lam).fit(X[tr], Y[tr], M0, feat_idx, mu, sd)
        pred[i] = mdl.predict(X[i:i+1])[0]
    rmse = np.sqrt(np.nanmean((pred - Y) ** 2, axis=0))
    return rmse, pred


def loo_structured_conf(X, y, m, lam_vec, scope_idx):
    n = len(y); pred = np.zeros(n)
    Xs = X[:, scope_idx]; gmu = Xs.mean(0); gsd = Xs.std(0)
    for i in range(n):
        tr = [k for k in range(n) if k != i]
        mdl = StructuredModel().fit(X[tr], y[tr], m, scope_idx, lam_vec=lam_vec, mu=gmu, sd=gsd)
        pred[i] = mdl.predict(X[i:i+1])[0]
    rmse = np.sqrt(np.mean((pred - y) ** 2))
    return rmse, pred
