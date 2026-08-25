# -*- coding: utf-8 -*-
"""
혼합물 반응 모형 — 배합 x 에서 반응 y 를 예측하고, 목표 y* 에 맞는 배합을 제안한다.

WHY THIS REPLACES THE AFFINE PREDICTOR
--------------------------------------
기존 propose.py 는 y = a + Bx 를 자유변수 회귀로 풀었다. 배합은 자유변수가 아니다.

    Σx_i = T  (배치 총량)

이 제약 때문에 세 가지가 깨져 있었다. 실제로 확인한 값이다.

    설계행렬 [1 | X]   열 7 · rank 6   → 절편이 식별 불가 (x 열의 합이 상수)
    propose_recipe     합계 100 → 83.05 → 제안된 배합이 배합이 아님
    parsimony_trim     합계 3.69        → 완전히 붕괴

근본 원인은 하나다. **혼합물에서 "재료 j 를 1 올린다" 는 문장은 그 자체로 불완전하다.**
무엇을 1 줄이는지 말하지 않으면 정의되지 않는다. 그래서 "j 의 효과" 라는 것은 절대적
으로 존재하지 않고, 항상 "무엇을 밀어내며" 라는 기준이 필요하다.

FILLER-REFERENCED PARAMETERIZATION
----------------------------------
Scheffé 표준형(절편 없이 y = Σβ_i x_i)도 옳지만, 실무 감각과 맞는 것은 필러 기준이다.
물(또는 지정한 필러) w 를 잔량으로 두면

    x_w = T - Σ_{j≠w} x_j

를 대입하여

    y = β_w T + Σ_{j≠w} (β_j - β_w) x_j
      = α + Σ_{j≠w} γ_j x_j            ,  γ_j = β_j - β_w

  · 자유변수는 q = p-1 개. 절편 α 는 T 가 고정이므로 식별된다
  · γ_j 의 뜻: **물을 밀어내며 j 를 1 단위 올릴 때 y 의 변화**
    이것이 개발자가 실제로 하는 조작이고, DoE 의 water auto-balance 와도 일치한다
  · 형태가 a + Bx 그대로라 기존 코드와 형식 호환된다. 다른 것은 x 에서 필러를 뺀다는 점뿐

MULTIVARIATE, NOT ONE-AT-A-TIME
-------------------------------
기존 코드는 속성마다 따로 적합했다. 반응들은 독립이 아니다 — 점도가 오르면 클링도
오른다. 따로 적합하면 두 가지를 잃는다.

  1. 목표 거리를 유클리드로 재게 되어 **상관된 반응에 이중으로 벌점**을 준다
  2. 한 반응의 관측이 상관된 다른 반응의 추정을 돕지 못한다

여기서는 Y 를 함께 적합하고 잔차 공분산 Σ 를 추정한다. 목표 거리는 마할라노비스
(y-y*)ᵀ Σ⁻¹ (y-y*) 로 잰다.

SMALL n
-------
실험은 5~20 회, 재료는 10~30 종. p > n 이 보통이다. 그래서

  · 사전으로의 능선회귀(ridge-to-prior). Λ 가 크면 사전, 작으면 데이터
  · Σ 는 Ledoit-Wolf 방식으로 대각으로 수축. n < m 이면 표본공분산이 특이해진다
  · 예측 분산을 함께 낸다. 점추정만 내면 "이 제안이 얼마나 믿을 만한가" 를 말할 수 없다

WHAT THIS MODULE DOES NOT DO
----------------------------
  · 비선형·상호작용: 지금은 1차. Scheffé 2차항은 add_interactions 로 열어 둠
  · 순서형 반응: JAR 1-5 와 -3..+3 은 순서형인데 여기서는 연속으로 다룬다.
    척도 끝(1 또는 5)에 몰린 데이터에서는 편향이 생긴다. 별도 처리 필요
  · 시간 의존: 침전·산패는 y(x, t) 다. T2 설계와 함께 다룰 것
"""
from __future__ import annotations

import numpy as np


def _as_lambda(prior_precision, q, m, default=1.0):
    """
    사전 정밀도 Λ 를 (q, m) 으로 정규화한다.

    온톨로지는 확신도를 **(재료 × 반응) 엣지마다** 정의한다. 예전에는 이 모듈이
    Λ 를 (q,) 로만 받아서, 호출부가 재료별 최솟값으로 축약해 넘겨야 했다.
    실측해보니 그 축약이 {0.4, 2.0, 8.0} 세 값을 **한 값으로** 뭉갰다 —
    사전지식의 강약 구조가 통째로 사라진다. 그래서 (q, m) 을 받는다.

    (q,) 도 계속 받는다. 그 경우 모든 반응에 같은 정밀도를 쓴다는 뜻으로 넓힌다.
    """
    if prior_precision is None:
        return np.full((q, m), float(default))
    lam = np.asarray(prior_precision, float)
    if lam.ndim == 0:
        return np.full((q, m), float(lam))
    if lam.ndim == 1:
        if lam.shape[0] != q:
            raise ValueError(
                f"prior_precision 의 길이가 {lam.shape[0]} 입니다. 자유변수 개수 q={q} 와 "
                f"같아야 합니다 (필러 제외).")
        return np.repeat(lam[:, None], m, axis=1)
    if lam.shape != (q, m):
        raise ValueError(
            f"prior_precision 의 모양이 {lam.shape} 입니다. (q,)=({q},) 또는 "
            f"(q, m)=({q}, {m}) 여야 합니다.")
    return lam


# =============================================================================
# 모형
# =============================================================================
class MixtureModel:
    """
    y = ȳ + (z - z̄) Γ        z = 필러를 제외한 자유 배합 벡터 (q = p-1)

    적합:  Γ̂ = (ZᶜᵀZᶜ + Λ)⁻¹ (ZᶜᵀYᶜ + Λ Γ₀)
           사전 Γ₀ 와 사전 정밀도 Λ 는 밖에서 준다 (온톨로지든 사람이든)
    """

    def __init__(self, names, filler, total=100.0):
        self.names = list(names)
        if filler not in self.names:
            raise ValueError(f"필러 '{filler}' 가 재료 목록에 없습니다")
        self.filler = filler
        self.fi = self.names.index(filler)
        self.free = [j for j in range(len(self.names)) if j != self.fi]
        self.total = float(total)
        self.fitted = False

    # ------------------------------------------------------------------ 도구
    def to_free(self, X):
        """전체 배합 → 자유 배합. 필러 열을 뺀다."""
        X = np.atleast_2d(np.asarray(X, float))
        return X[:, self.free]

    def to_full(self, Z):
        """자유 배합 → 전체 배합. 필러를 잔량으로 채운다."""
        Z = np.atleast_2d(np.asarray(Z, float))
        X = np.zeros((Z.shape[0], len(self.names)))
        X[:, self.free] = Z
        X[:, self.fi] = self.total - Z.sum(1)
        return X

    def check_total(self, X, tol=1e-6):
        s = np.atleast_2d(np.asarray(X, float)).sum(1)
        return np.all(np.abs(s - self.total) < tol)

    # ------------------------------------------------------------------ 적합
    def fit(self, X, Y, prior=None, prior_precision=None, ridge=1.0,
            shrink=None):
        """
        X (n,p) 전체 배합 · Y (n,m) 반응
        prior (q,m)            γ 의 사전 평균. 없으면 0
        prior_precision (q,)   엣지별 정밀도 Λ 대각. 없으면 ridge 로 균일
        shrink                 Σ 수축 계수 δ ∈ [0,1]. None 이면 자동
        """
        X = np.atleast_2d(np.asarray(X, float))
        Y = np.atleast_2d(np.asarray(Y, float))
        if not self.check_total(X, tol=1e-4):
            raise ValueError(
                f"배합 합계가 {self.total} 이 아닙니다: {np.unique(np.round(X.sum(1),3))}. "
                "혼합물 모형은 총량이 고정된 데이터에서만 의미가 있습니다.")
        Z = self.to_free(X)
        n, q = Z.shape
        m = Y.shape[1]

        # 표준화. 능선 벌점은 스케일에 의존하므로, 표준화하지 않으면 단위가 큰
        # 재료(물 g)와 작은 재료(잔탄검 g)에 사실상 다른 세기의 벌점이 걸린다.
        # 사전도 "1 표준편차당 효과" 로 주어지므로 같은 단위로 맞춘다.
        self.zbar = Z.mean(0)
        self.zsd = Z.std(0)
        self.zsd[self.zsd < 1e-9] = 1.0
        self.ybar = Y.mean(0)
        Zc = (Z - self.zbar) / self.zsd
        Yc = Y - self.ybar

        G0 = np.zeros((q, m)) if prior is None else np.asarray(prior, float).reshape(q, m)
        self.Lam = _as_lambda(prior_precision, q, m, default=ridge)   # (q, m)

        # 반응 열마다 따로 푼다. Λ 가 열마다 다르므로 하나의 A 로 묶을 수 없다.
        # 열끼리는 독립이라 이렇게 푸는 것이 정확하다(근사가 아니다).
        XtX = Zc.T @ Zc
        XtY = Zc.T @ Yc
        self.Ainv = np.empty((m, q, q))
        self.G = np.empty((q, m))
        for k in range(m):
            Lk = np.diag(self.Lam[:, k])
            self.Ainv[k] = np.linalg.inv(XtX + Lk)
            self.G[:, k] = self.Ainv[k] @ (XtY[:, k] + Lk @ G0[:, k])

        # 잔차 공분산 — 반응끼리의 상관이 여기 담긴다
        E = Yc - Zc @ self.G
        # 유효 자유도도 열마다 다르다. 하나의 Σ 를 추정하므로 평균을 쓴다.
        dof = max(n - float(np.mean([np.trace(Zc @ self.Ainv[k] @ Zc.T)
                                     for k in range(m)])), 1.0)
        S = (E.T @ E) / dof
        if m > 1:
            # 소표본에서 표본공분산은 특이하거나 극단적이다. 대각으로 수축한다.
            d = np.diag(np.diag(S))
            if shrink is None:
                # 관측이 반응 수보다 적을수록 세게 수축
                shrink = float(np.clip(m / max(n, 1), 0.0, 0.9))
            S = (1.0 - shrink) * S + shrink * d
        self.Sigma = S + 1e-12 * np.eye(m)
        self.Sigma_inv = np.linalg.inv(self.Sigma)
        self.n, self.q, self.m = n, q, m
        self.fitted = True
        return self

    def fit_prior_only(self, prior, prior_precision=None, sigma=None,
                       zbar=None, zsd=None, ybar=None):
        """
        데이터 0 건에서 사전만으로 세운다. 첫 제안을 내려면 이것이 필요하다.

        지금까지 이 경로가 없어서 닭·달걀이었다 — 제안하려면 데이터가 필요하고,
        데이터는 제안된 배합을 만들어봐야 생긴다.

        zsd 는 반드시 줘야 한다
        ------------------------
        온톨로지 사전은 "**1 표준편차**당 효과" 로 정의된다. 예전에는 이 함수가
        zsd 를 조용히 1 로 두었고, 그러면 모형이 "1 퍼센트포인트 = 1 표준편차" 로
        읽는다. 실측한 결과가 이렇다.

            알룰로스 20 pp  ->  단맛 +20.0      (관능 척도는 ±3 에서 포화한다)

        상한의 6.7 배다. 그래서 옵티마이저는 "이미 너무 달다" 고 판단해 감미료를
        빼버렸다. 멈추지 않고 틀리는 종류의 오류라서 기본값을 없앴다.

        zsd 로 넘길 값: 각 재료의 **작업 범위 폭 / 4** 정도가 무난하다(범위를
        대략 ±2 SD 로 보는 것). 범위를 아직 모르면 zsd="unit" 로 명시적으로
        원단위 해석을 선택할 수 있다 — 사전이 이미 원단위일 때만 옳다.
        """
        G0 = np.asarray(prior, float)
        if G0.ndim != 2:
            raise ValueError(f"prior 는 (q, m) 2차원이어야 합니다. 받은 모양: {G0.shape}")
        q, m = G0.shape

        # --- B3: 행 수 검증. 자유변수는 필러를 제외한 p-1 개다.
        # 예전에는 검증이 없어서, 팔레트 전체 행수(필러 포함)를 넘기면 여기서는
        # 통과하고 한참 뒤 propose() 안에서 broadcast 오류로 터졌다.
        q_free = len(self.free)
        if q != q_free:
            raise ValueError(
                f"prior 의 행 수가 {q} 입니다. 자유변수 개수 {q_free} 여야 합니다 "
                f"(재료 {len(self.names)}종에서 필러 '{self.filler}' 제외). "
                f"온톨로지 조립기가 팔레트 전체에 대해 Γ₀ 를 만들었다면 필러 행을 "
                f"빼고 넘기세요 — 스펙 불변식 8 에 따라 계수는 이미 필러 기준입니다.")

        # --- B1: 스케일을 명시하게 한다
        if zsd is None:
            raise ValueError(
                "zsd 를 지정해야 합니다. 사전 계수는 '1 표준편차당 효과' 로 정의되므로 "
                "재료의 작업 스케일 없이는 해석할 수 없습니다. 재료별 작업 범위 폭의 "
                "1/4 정도를 넘기거나, 사전이 이미 원단위라면 zsd=\"unit\" 로 명시하세요.")
        if isinstance(zsd, str):
            if zsd != "unit":
                raise ValueError(f"zsd 문자열은 \"unit\" 만 허용합니다. 받은 값: {zsd!r}")
            zsd_arr = np.ones(q)
        else:
            zsd_arr = np.asarray(zsd, float)
            if zsd_arr.ndim == 0:
                zsd_arr = np.full(q, float(zsd_arr))
            if zsd_arr.shape != (q,):
                raise ValueError(f"zsd 의 모양이 {zsd_arr.shape} 입니다. ({q},) 여야 합니다.")
            if np.any(zsd_arr <= 0):
                raise ValueError("zsd 는 모두 양수여야 합니다.")

        self.zbar = np.zeros(q) if zbar is None else np.asarray(zbar, float)
        self.zsd = zsd_arr
        self.ybar = np.zeros(m) if ybar is None else np.asarray(ybar, float)
        self.G = G0

        # --- B4: Λ 를 (q, m) 으로. 데이터가 없으므로 A = Λ 이고 Ainv = 1/Λ 다.
        self.Lam = _as_lambda(prior_precision, q, m, default=1.0)
        self.Ainv = np.stack([np.diag(1.0 / self.Lam[:, k]) for k in range(m)])

        self.Sigma = (np.eye(m) if sigma is None else np.asarray(sigma, float))
        self.Sigma_inv = np.linalg.inv(self.Sigma)
        self.n, self.q, self.m = 0, q, m
        self.fitted = True
        return self

    # ------------------------------------------------------------------ 예측
    def predict(self, X, with_var=False):
        """X 는 전체 배합. (mean, var) 를 돌려준다."""
        Z = self.to_free(X)
        mu = self.ybar + ((Z - self.zbar) / self.zsd) @ self.G
        if not with_var:
            return mu
        # 사후 예측 분산: 계수 불확실성 + 잔차
        # Λ 가 반응마다 다르므로 지렛대도 반응마다 다르다. Ainv 는 (m, q, q) 다.
        Zc = (Z - self.zbar) / self.zsd
        lev = np.einsum("ij,kjl,il->ik", Zc, self.Ainv, Zc)         # (n, m) 지렛대
        s2 = np.diag(self.Sigma)[None, :]
        var = lev * s2 + s2
        return mu, var

    # ------------------------------------------------------------------ 방향성
    def direction(self, response_index=None):
        """
        각 재료가 이 반응을 어느 방향으로 얼마나 움직이는가.
        값의 뜻: **필러를 밀어내며 1 단위 올릴 때의 변화**.

        이 해석을 못 박아 두는 것이 중요하다. 혼합물에서 "재료의 효과" 는
        무엇을 밀어내느냐에 따라 달라지므로, 기준 없이 말하면 틀린 말이 된다.
        """
        # 원 단위로 환산: Γ 는 표준화 공간에서 적합됐다
        Graw = self.G / self.zsd[:, None]
        out = {}
        for k, j in enumerate(self.free):
            out[self.names[j]] = (Graw[k] if response_index is None
                                  else float(Graw[k, response_index]))
        return out


# =============================================================================
# 제안 — 목표 y* 에 도달하는 배합
# =============================================================================
def propose(model: MixtureModel, target, x0, lo=None, hi=None,
            weight=None, stay=0.02, iters=3000, lr=None, mask=None):
    """
    min_z  (ŷ(z) - y*)ᵀ W (ŷ(z) - y*) + stay·||z - z₀||²
    s.t.   lo ≤ z ≤ hi,   Σz ≤ T - lo_filler        (필러가 음수가 되지 않게)

    W 기본값은 Σ⁻¹ (마할라노비스). 상관된 반응에 이중 벌점을 주지 않기 위해서다.
    반환은 **전체 배합** 이며 합계는 항상 T 다.
    """
    if not model.fitted:
        raise RuntimeError("적합되지 않은 모형입니다")
    q = model.q
    x0 = np.asarray(x0, float)
    if not model.check_total(x0[None, :], tol=1e-4):
        raise ValueError(f"시작 배합의 합계가 {model.total} 이 아닙니다: {x0.sum()}")
    z0 = model.to_free(x0)[0]
    lo = np.zeros(q) if lo is None else np.asarray(lo, float)
    hi = np.full(q, model.total) if hi is None else np.asarray(hi, float)
    W = model.Sigma_inv if weight is None else np.asarray(weight, float)
    t = np.asarray(target, float)
    adj = np.ones(q, bool) if mask is None else np.asarray(mask, bool)

    # 학습률은 곡률에 맞춘다. 손으로 고른 lr 은 스케일이 바뀌면 발산하거나 멈춘다.
    Graw = model.G / model.zsd[:, None]          # 원 단위 기울기
    H = 2.0 * (Graw @ W @ Graw.T) + 2.0 * stay * np.eye(q)
    if lr is None:
        L = np.linalg.eigvalsh(H).max()
        lr = 1.0 / max(L, 1e-9)

    z = z0.copy()
    cap = model.total                      # Σz ≤ T (필러 ≥ 0)
    for _ in range(iters):
        r = model.ybar + ((z - model.zbar) / model.zsd) @ model.G - t
        g = 2.0 * (Graw @ (W @ r)) + 2.0 * stay * (z - z0)
        z = z - lr * g
        z[~adj] = z0[~adj]
        z = np.clip(z, lo, hi)
        # 단체(simplex) 사영 — 필러가 음수가 되면 비례 축소
        s = z.sum()
        if s > cap:
            over = s - cap
            room = np.maximum(z - lo, 0.0)
            tot = room.sum()
            if tot > 1e-12:
                z = z - room * (over / tot)
                z = np.clip(z, lo, hi)
    return model.to_full(z)[0]


def trim(model: MixtureModel, x, target, lo=None, tol=0.15, weight=None):
    """
    빼도 결과가 거의 안 변하는 재료를 뺀다. **뺀 양은 필러로 돌려준다** —
    그래야 합계가 유지된다. 기존 parsimony_trim 은 이 되돌림이 없어서
    합계가 100 에서 3.69 까지 무너졌다.
    """
    x = np.asarray(x, float).copy()
    q = model.q
    lo = np.zeros(q) if lo is None else np.asarray(lo, float)
    W = model.Sigma_inv if weight is None else np.asarray(weight, float)
    base = model.predict(x[None, :])[0]

    def cost(v):
        r = v - np.asarray(target, float)
        return float(r @ W @ r)

    c0 = cost(base)
    order = np.argsort([x[j] for j in model.free])      # 적게 든 것부터
    for k in order:
        j = model.free[k]
        if x[j] <= lo[k] + 1e-9:
            continue
        cand = x.copy()
        freed = cand[j] - lo[k]
        cand[j] = lo[k]
        cand[model.fi] += freed                        # ★ 필러로 되돌림
        if cost(model.predict(cand[None, :])[0]) - c0 < tol:
            x = cand
    return x


# =============================================================================
def selftest():
    rng = np.random.default_rng(0)
    names = ["chili", "sugar", "salt", "vinegar", "xanthan", "water"]
    T = 100.0
    fails = []

    Z = rng.uniform(0, 12, (16, 5))
    X = np.column_stack([Z, T - Z.sum(1)])
    # 진짜 관계: 필러 기준 계수. 반응끼리 상관되게 만든다.
    Gtrue = np.array([[2.0, 0.0, 0.2],
                      [-0.3, 1.5, 0.1],
                      [0.0, 0.0, 0.0],
                      [0.1, -0.2, 0.0],
                      [0.0, 0.0, 3.0]])
    Y = Z @ Gtrue + rng.normal(0, 0.15, (16, 3))

    m = MixtureModel(names, filler="water", total=T)
    m.fit(X, Y, ridge=0.5)

    # 1) 합계 제약 — 기존 코드가 깨뜨리던 것
    x0 = X[0]
    tgt = np.array([12.0, 9.0, 18.0])
    xp = propose(m, tgt, x0)
    if abs(xp.sum() - T) > 1e-6:
        fails.append(f"제안 배합 합계가 {xp.sum():.3f} (T={T} 이어야 함)")
    if (xp < -1e-9).any():
        fails.append("음수 성분이 나왔다")

    xt = trim(m, xp, tgt)
    if abs(xt.sum() - T) > 1e-6:
        fails.append(f"정리 후 합계가 {xt.sum():.3f}")

    # 2) 목표에 실제로 가까워지는가
    d0 = np.linalg.norm(m.predict(x0[None, :])[0] - tgt)
    d1 = np.linalg.norm(m.predict(xp[None, :])[0] - tgt)
    if d1 >= d0:
        fails.append(f"목표에 가까워지지 않았다: {d0:.2f} → {d1:.2f}")

    # 3) 방향성이 참값의 부호와 맞는가
    d = m.direction(0)
    if d["chili"] <= 0 or d["sugar"] >= 0:
        fails.append(f"방향성 부호가 틀렸다: chili={d['chili']:.2f} sugar={d['sugar']:.2f}")

    # 4) 반응 공분산이 실제로 추정되는가
    if m.Sigma.shape != (3, 3) or not np.all(np.linalg.eigvalsh(m.Sigma) > 0):
        fails.append("Σ 가 양정치가 아니다")

    # 5) 예측 불확실성이 나오는가 — 데이터에서 먼 배합일수록 커야 한다
    mu, var = m.predict(np.vstack([x0, m.to_full(np.full((1, 5), 11.0))[0]]), with_var=True)
    if not (var[1] > var[0]).all():
        fails.append("외삽 지점의 분산이 더 크지 않다")

    # 6) 데이터 0 건에서도 제안이 나오는가 — 닭·달걀을 푸는 경로
    # Gtrue 는 합성 데이터를 만들 때 쓴 계수라 이미 원단위다 → zsd="unit"
    m0 = MixtureModel(names, filler="water", total=T).fit_prior_only(
        prior=Gtrue, prior_precision=np.full(5, 2.0), zsd="unit")
    xp0 = propose(m0, tgt, x0)
    if abs(xp0.sum() - T) > 1e-6:
        fails.append("사전만으로 낸 제안의 합계가 어긋난다")
    if np.linalg.norm(m0.predict(xp0[None, :])[0] - tgt) >= \
       np.linalg.norm(m0.predict(x0[None, :])[0] - tgt):
        fails.append("사전만으로는 목표에 가까워지지 않는다")

    # 7) 합계가 안 맞는 데이터는 거부해야 한다
    try:
        MixtureModel(names, filler="water", total=T).fit(X * 0.9, Y)
        fails.append("합계가 틀린 데이터를 받아들였다")
    except ValueError:
        pass

    return fails


if __name__ == "__main__":
    f = selftest()
    print("자체 점검:", "통과" if not f else f)
