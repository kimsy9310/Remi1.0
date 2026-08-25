# -*- coding: utf-8 -*-
"""
웜루프 — 온톨로지 사전값을 실측으로 보정하고, 다음 실험을 제안한다.

한 바퀴
-------
    온톨로지 사전 Γ₀        무엇이 무엇을 움직이는지에 대한 현재 믿음
        ↓  + 실측 (X, Y)
    사후 Γ̂ = (ZᵀZ + Λ)⁻¹(ZᵀY + ΛΓ₀)    데이터가 사전을 얼마나 밀어냈는가
        ↓
    다음 제안                 목표에 가장 가까워지는 배합
        ↓
    (랩에서 만들어 평가) → 데이터에 추가 → 다시 위로

Λ 가 이 루프의 손잡이다. 확신도 high(8) 인 엣지는 데이터 8건어치의 무게로 버티고,
low(0.4) 인 엣지는 거의 즉시 데이터에 자리를 내준다. 그래서 데이터가 침묵하는
축은 사전지식이 보존되고, 데이터가 많은 축은 실측으로 정교해진다.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from formulator.mixture import MixtureModel, propose


@dataclass
class WarmLoopResult:
    model: MixtureModel               # 데이터로 적합된 모형
    prior_model: MixtureModel         # 사전만으로 세운 모형(비교용)
    names: list
    free: list                        # 필러 제외 재료
    filler: str
    y_terms: list
    Gamma_prior: np.ndarray           # (q, m) 온톨로지 사전
    Gamma_post: np.ndarray            # (q, m) 실측 보정 후
    Lambda: np.ndarray                # (q, m) 엣지별 확신도
    n: int
    eff_directions: int               # 실제로 탐색된 독립 방향 수
    warnings: list = field(default_factory=list)

    # ------------------------------------------------------------------ 비교
    def shifts(self, top=None):
        """사전 대비 가장 많이 움직인 (재료, 축) 목록. 배운 것이 무엇인지."""
        out = []
        for j, g in enumerate(self.free):
            for k, t in enumerate(self.y_terms):
                p, q = self.Gamma_prior[j, k], self.Gamma_post[j, k]
                if abs(p) < 1e-9 and abs(q) < 1e-9:
                    continue
                out.append(dict(ingredient=g, axis=t, prior=float(p), post=float(q),
                                shift=float(q - p), lam=float(self.Lambda[j, k]),
                                flipped=bool(p * q < 0 and abs(p) > 1e-9)))
        out.sort(key=lambda d: -abs(d["shift"]))
        return out[:top] if top else out

    def learned_from_silence(self):
        """사전이 없었는데(0) 데이터가 채운 칸 — 순수하게 실측이 만든 지식."""
        return [d for d in self.shifts() if abs(d["prior"]) < 1e-9 and abs(d["post"]) > 0.05]

    def contradicted(self):
        """사전과 부호가 뒤집힌 칸 — 온톨로지를 고쳐야 할 후보."""
        return [d for d in self.shifts() if d["flipped"]]

    def report(self):
        L = [f"실측 {self.n}건으로 적합 · 재료 {len(self.free)}종(자유변수) · 축 {len(self.y_terms)}개",
             f"실제 탐색된 독립 방향 {self.eff_directions}개 "
             f"— 샘플 수({self.n})가 아니라 이 값이 배울 수 있는 양을 정합니다"]
        c = self.contradicted()
        if c:
            L.append(f"사전과 부호가 뒤집힌 칸 {len(c)}개 (온톨로지 검토 후보)")
        s = self.learned_from_silence()
        if s:
            L.append(f"사전이 비어 있던 칸을 데이터가 채운 것 {len(s)}개")
        L += self.warnings
        return "\n".join("  " + x for x in L)


def _align(built, y_terms):
    """조립된 Γ₀ 에서 데이터가 가진 축만 골라낸다."""
    idx = []
    for t in y_terms:
        if t not in built.y_terms:
            raise KeyError(
                f"축 {t} 가 프로파일의 core 카드에 없습니다. "
                f"프로파일 축: {built.y_terms}")
        idx.append(built.y_terms.index(t))
    return built.Gamma0[:, idx], built.Lambda[:, idx], built.Sigma0[np.ix_(idx, idx)]


def effective_directions(Z, tol=0.05):
    """
    배합 행렬이 실제로 탐색한 독립 방향 수.

    시제품 개수는 정보량이 아니다 — 재료를 함께 움직이면 여러 런이 같은 방향을
    반복한다. HANDOFF 가 "시제품 15개도 실제론 ~6방향" 이라 적은 그 값이다.
    """
    Zc = Z - Z.mean(0)
    sd = Zc.std(0)
    sd[sd < 1e-12] = 1.0
    s = np.linalg.svd(Zc / sd, compute_uv=False)
    if s.size == 0 or s[0] < 1e-12:
        return 0
    return int((s / s[0] > tol).sum())


def run(onto, data, profile, bounds=None):
    """온톨로지 사전 + 실측 → 보정된 모형."""
    built = onto.build(profile, palette=list(data.names), bounds=bounds,
                       x0=data.X[0] if len(data.X) else None)
    G0, lam, S0 = _align(built, data.y_terms)

    free = [n for n in built.palette if n != built.filler]
    # dataio 의 열 순서와 built.palette 의 순서를 맞춘다
    order = [data.names.index(g) for g in built.palette]
    X = data.X[:, order]

    warns = list(built.warnings)

    prior_model = MixtureModel(built.palette, filler=built.filler, total=100.0)
    prior_model.fit_prior_only(prior=G0, prior_precision=lam, sigma=S0,
                               zbar=built.zbar, zsd=built.zsd)

    model = MixtureModel(built.palette, filler=built.filler, total=100.0)
    model.fit(X, data.Y, prior=G0, prior_precision=lam)

    eff = effective_directions(model.to_free(X))
    q = len(free)
    if eff < q:
        warns.append(
            f"자유변수는 {q}개인데 데이터가 탐색한 방향은 {eff}개입니다. "
            f"차이만큼은 사전값이 그대로 남습니다 — 틀렸다는 뜻이 아니라 "
            f"이 데이터로는 확인되지 않았다는 뜻입니다.")
    if len(X) <= q:
        warns.append(
            f"샘플 {len(X)}건 ≤ 자유변수 {q}개입니다. 사전이 없으면 풀 수 없는 문제이고, "
            f"지금은 Λ 가 그 자리를 메우고 있습니다.")

    return WarmLoopResult(
        model=model, prior_model=prior_model, names=list(built.palette),
        free=free, filler=built.filler, y_terms=list(data.y_terms),
        Gamma_prior=G0, Gamma_post=model.G, Lambda=lam,
        n=len(X), eff_directions=eff, warnings=warns)


def suggest(res: WarmLoopResult, target, x0, bounds=None, stay=0.02, iters=3000):
    """
    목표 관능 변화에 맞는 다음 배합.

    target : {L.* : 변화량} 또는 길이 m 배열. 0 = 유지.
    bounds : {ING.* : (lo, hi)} — 없으면 상한이 없어 물리적으로 불가능한 값이
             나올 수 있다(온톨로지 G5). 되도록 넘길 것.
    """
    if isinstance(target, dict):
        unknown = [k for k in target if k not in res.y_terms]
        if unknown:
            raise KeyError(f"이 모형의 축이 아닙니다: {unknown}. 가능: {res.y_terms}")
        t = np.zeros(len(res.y_terms))
        for k, v in target.items():
            t[res.y_terms.index(k)] = float(v)
    else:
        t = np.asarray(target, float)

    x0 = np.asarray(x0, float)
    lo = hi = None
    if bounds:
        lo = np.array([float(bounds.get(g, (0.0, 100.0))[0]) for g in res.free])
        hi = np.array([float(bounds.get(g, (0.0, 100.0))[1]) for g in res.free])
    return propose(res.model, target=t, x0=x0, lo=lo, hi=hi, stay=stay, iters=iters)


def compare_prediction(res: WarmLoopResult, x):
    """같은 배합에 대해 사전만의 예측과 실측 보정 후 예측을 나란히."""
    x = np.asarray(x, float)[None, :]
    return dict(zip(res.y_terms,
                    zip(np.round(res.prior_model.predict(x)[0], 2).tolist(),
                        np.round(res.model.predict(x)[0], 2).tolist())))
