# -*- coding: utf-8 -*-
"""
배합 제안 — mixture.MixtureModel 로 위임하는 얇은 층.

WHAT CHANGED (2026-08-13)
-------------------------
이 파일은 원래 y = a + Bx 를 자유변수 회귀로 풀었다. 배합은 자유변수가 아니다.

    Σ x_i = T   (배치 총량)

이 제약 때문에 세 가지가 성립하지 않았다. 실측값이다.

    설계행렬 [1 | X]   열 7 · rank 6      절편이 식별 불가
    propose_recipe     합계 100 → 97.93   제안된 배합이 배합이 아님
    parsimony_trim     합계 → 19.22       재료를 0 으로 만들며 그 양을 어디에도
                                          돌려주지 않아 배치가 사라짐

수학은 mixture.py 에 있다. 이 파일은 기존 호출부가 그대로 돌아가도록 이름과
시그니처만 유지하는 어댑터다.

WHY KEEP THE OLD NAMES
----------------------
run_propose.py · run_doe.py · run_reps.py · run_integrated.py 가 이 이름들을 쓴다.
이름을 바꾸면 그 스크립트들이 죽고, 죽은 스크립트는 고치지 않게 된다. 이름을 두고
속을 갈면 스크립트는 그대로 돌면서 결과만 올바르게 된다.

FAILS LOUDLY
------------
데이터가 혼합물 제약을 만족하지 않으면 예외를 낸다. 예전에는 그냥 계산해서 합계가
어긋난 답을 내놓았고, 숫자가 그럴듯해서 아무도 눈치채지 못했다.
"""
from __future__ import annotations

import numpy as np

from .mixture import MixtureModel, propose as _mix_propose, trim as _mix_trim
from .structured import MAG, CONF


# =============================================================================
def _infer_filler(names, X, total=None):
    """
    필러(잔량으로 채우는 성분)를 찾는다. 보통 물이다.

    기준 둘을 쓴다 — 이름에 water 가 있거나, 다른 성분의 합과 가장 강하게
    음의 상관을 가지는 열. 후자가 본질적 정의다: 필러는 나머지가 늘면 줄어든다.
    """
    lower = [str(n).lower() for n in names]
    for j, n in enumerate(lower):
        if "water" in n or n in ("물", "정제수"):
            return j
    rest = X.sum(1)[:, None] - X
    corr = [np.corrcoef(X[:, j], rest[:, j])[0, 1] if X[:, j].std() > 1e-9 else 0.0
            for j in range(X.shape[1])]
    return int(np.argmin(corr))


def _prior_matrix(PRIOR, names, snames, free_idx, default_conf="medium"):
    """
    {속성: {재료: 크기 또는 (크기, 확신도)}}  →  (Γ₀ (q,m), Λ (q,))

    크기는 -3..3 이고 MAG 로 1 표준편차당 효과로 환산된다. mixture 는 표준화
    공간에서 적합하므로 단위가 그대로 맞는다.

    Λ 는 속성별로 다를 수 있으나 mixture 는 재료별 하나만 받는다. 같은 재료가
    여러 속성에서 다른 확신도를 가지면 **가장 약한 확신도**를 쓴다 — 강한 쪽을
    쓰면 근거가 약한 엣지까지 사전에 붙들려 데이터가 못 움직인다.
    """
    q, m = len(free_idx), len(snames)
    G0 = np.zeros((q, m))
    lam = np.full(q, CONF["low"])
    for c, at in enumerate(snames):
        row = PRIOR.get(at, {}) or {}
        for k, j in enumerate(free_idx):
            e = row.get(names[j])
            if e is None:
                continue
            if isinstance(e, (tuple, list)):
                val, conf = e[0], e[1]
            else:
                val, conf = e, default_conf
            G0[k, c] = np.sign(val) * MAG[abs(int(val))]
            lam[k] = min(lam[k], CONF.get(conf, CONF["medium"])) \
                if lam[k] > CONF["low"] else max(lam[k], CONF.get(conf, CONF["medium"]))
    return G0, lam


# =============================================================================
class SensoryPredictor:
    """
    기존 이름 유지. 속은 MixtureModel 이다.

    옛 버전은 속성마다 따로 적합했다. 반응들은 독립이 아니어서 (점도가 오르면
    클링도 오른다) 따로 적합하면 목표 거리를 유클리드로 재게 되고, 상관된 반응에
    이중으로 벌점을 준다. 이제 함께 적합하고 잔차 공분산 Σ 를 추정한다.
    """

    def __init__(self, names, filler=None, total=None):
        self.names = list(names)
        self._filler = filler
        self._total = total
        self.model = None

    def fit(self, X, Y, snames, PRIOR, ridge=None):
        X = np.atleast_2d(np.asarray(X, float))
        Y = np.atleast_2d(np.asarray(Y, float))
        self.snames = list(snames)

        total = self._total
        if total is None:
            s = X.sum(1)
            total = float(np.median(s))
            if s.std() > 1e-6 * max(abs(total), 1.0):
                raise ValueError(
                    f"배합 합계가 행마다 다릅니다 (표준편차 {s.std():.4g}). "
                    "혼합물 모형은 총량이 고정된 데이터에서만 성립합니다. "
                    "빈 행이 섞여 있지 않은지, 단위가 섞이지 않았는지 보세요.")
        fi = self._filler
        if fi is None:
            fi = _infer_filler(self.names, X, total)
        if isinstance(fi, (int, np.integer)):
            fi = self.names[int(fi)]
        self.filler = fi
        self.total = total

        self.model = MixtureModel(self.names, filler=fi, total=total)
        free = self.model.free
        G0, lam = _prior_matrix(PRIOR, self.names, self.snames, free)
        if ridge is not None:
            lam = np.full(len(free), float(ridge))
        self.model.fit(X, Y, prior=G0, prior_precision=lam)
        return self

    # ---- 예측 -------------------------------------------------------------
    def predict(self, x, with_var=False):
        x = np.atleast_2d(np.asarray(x, float))
        out = self.model.predict(x, with_var=with_var)
        if with_var:
            mu, var = out
            return (mu[0], var[0]) if mu.shape[0] == 1 else (mu, var)
        return out[0] if out.shape[0] == 1 else out

    def direction(self, response=None):
        """각 재료가 반응을 어느 방향으로 움직이나 (필러를 밀어내는 기준)."""
        idx = None
        if response is not None:
            idx = response if isinstance(response, int) else self.snames.index(response)
        return self.model.direction(idx)

    # ---- 옛 코드가 참조하던 affine 형태 -----------------------------------
    @property
    def B(self):
        """전체 배합 좌표에서의 기울기. 필러 열은 0 (잔량이므로 자유롭지 않다)."""
        Braw = (self.model.G / self.model.zsd[:, None]).T          # (m, q)
        full = np.zeros((len(self.snames), len(self.names)))
        for k, j in enumerate(self.model.free):
            full[:, j] = Braw[:, k]
        return full

    @property
    def a(self):
        z = self.model.zbar
        return self.model.ybar - (z / self.model.zsd) @ self.model.G


# =============================================================================
def _free_bounds(model, lo, hi):
    """전체 좌표로 준 상하한을 자유 좌표로 줄인다."""
    lo = np.asarray(lo, float)
    hi = np.asarray(hi, float)
    if lo.size == len(model.names):
        lo = lo[model.free]
    if hi.size == len(model.names):
        hi = hi[model.free]
    return lo, hi


def propose_recipe(pred: SensoryPredictor, target, lo, hi, x0,
                   reg_stay=0.02, iters=3000, lr=None, adjustable=None,
                   weight=None):
    """
    목표 반응에 맞는 배합. **반환 배합의 합계는 항상 총량과 같다.**

    옛 버전은 여기서 합계가 무너졌다. 지금은 단체(simplex) 사영이 매 반복마다
    걸리므로 구조적으로 무너질 수 없다.
    """
    m = pred.model
    lof, hif = _free_bounds(m, lo, hi)
    mask = None
    if adjustable is not None:
        adjustable = np.asarray(adjustable, bool)
        mask = adjustable[m.free] if adjustable.size == len(m.names) else adjustable
    return _mix_propose(m, target, np.asarray(x0, float), lo=lof, hi=hif,
                        weight=weight, stay=reg_stay, iters=iters, lr=lr, mask=mask)


def parsimony_trim(pred: SensoryPredictor, x, lo, hi, target, tol=0.15,
                   weight=None):
    """
    영향이 작은 재료를 뺀다. **뺀 양은 필러로 돌려준다.**
    옛 버전은 이 되돌림이 없어 합계가 100 에서 19 까지 무너졌다.
    """
    m = pred.model
    lof, _ = _free_bounds(m, lo, hi)
    return _mix_trim(m, np.asarray(x, float), target, lo=lof, tol=tol, weight=weight)


def propose_integrated(pred: SensoryPredictor, target, lo, hi, x0, onto=None,
                       col2ing=None, defect_cols=None, **kw):
    """
    제안 + 결함 재료 치환. 치환은 온톨로지가 있을 때만 시도하고, 없으면 제안만 한다.
    이 모듈은 이제 온톨로지에 의존하지 않는다 — 없으면 없는 대로 돈다.
    """
    x = propose_recipe(pred, target, lo, hi, x0, **kw)
    swaps = []
    if onto is None or col2ing is None or not defect_cols:
        return x, swaps
    try:
        from .substitution import suggest_substitutes
    except Exception:
        return x, swaps
    m = pred.model
    for c in defect_cols:
        ci = pred.snames.index(c) if isinstance(c, str) else c
        d = m.direction(ci)
        worst = max(((n, v) for n, v in d.items()
                     if x[m.names.index(n)] > 1e-9), key=lambda t: t[1], default=None)
        if not worst or worst[1] <= 0:
            continue
        ing = col2ing.get(worst[0])
        if not ing:
            continue
        try:
            alts = suggest_substitutes(onto, ing)
        except Exception:
            alts = []
        if alts:
            swaps.append({"from": worst[0], "to": alts[0], "response": pred.snames[ci],
                          "effect": round(float(worst[1]), 3)})
    return x, swaps
