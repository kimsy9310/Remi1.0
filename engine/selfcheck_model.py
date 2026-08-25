# -*- coding: utf-8 -*-
"""
모델 자체 점검 — 수학이 성립하는지 매번 확인한다.

    py selfcheck_model.py

여기 있는 검사는 전부 실제로 겪은 고장에서 나왔다. 가장 큰 것은 이것이다.

    배합은 자유변수가 아니다.  Σ x_i = T

이 제약을 안 지킨 채로 회귀와 최적화를 돌리면, 숫자는 그럴듯하게 나오는데
제안된 배합의 합계가 안 맞는다. 겉보기로는 정상이라 오래 못 잡았다.
"""
import os
import sys

import numpy as np

# 어느 디렉터리에서 실행해도 같게 동작하도록 자기 위치를 기준으로 잡는다.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
MIXTURE_SRC = os.path.join(_HERE, "formulator", "mixture.py")

OK, BAD = [], []


def check(name, cond, detail=""):
    (OK if cond else BAD).append((name, detail))


def main():
    try:
        from formulator.mixture import MixtureModel, propose, trim
        from formulator import propose as P
    except Exception as e:
        print(f"[치명] 모듈을 불러오지 못했습니다: {e}")
        return 1

    # ---------------------------------------------------------- mixture 코어
    f = __import__("formulator.mixture", fromlist=["selftest"]).selftest()
    check("혼합물 모형 자체 점검", not f, str(f))

    rng = np.random.default_rng(7)
    names = ["a", "b", "c", "d", "water"]
    T = 100.0
    Z = rng.uniform(0, 15, (18, 4))
    X = np.column_stack([Z, T - Z.sum(1)])
    Gt = np.array([[2.0, 0.1], [-0.5, 1.2], [0.0, 0.0], [0.3, -0.4]])
    Y = Z @ Gt + rng.normal(0, 0.2, (18, 2))

    m = MixtureModel(names, filler="water", total=T).fit(X, Y, ridge=0.5)
    x0 = X[0]
    tgt = np.array([14.0, 8.0])

    # ---- 합계 보존. 이것이 무너지면 제안이 배합이 아니다
    xp = propose(m, tgt, x0)
    check("제안 배합의 합계가 총량과 같음", abs(xp.sum() - T) < 1e-6, f"{xp.sum():.4f}")
    check("제안 배합에 음수가 없음", (xp >= -1e-9).all())

    xt = trim(m, xp, tgt)
    check("정리 후에도 합계가 유지됨", abs(xt.sum() - T) < 1e-6, f"{xt.sum():.4f}")

    # ---- 목표에 실제로 가까워지는가
    d0 = np.linalg.norm(m.predict(x0[None, :])[0] - tgt)
    d1 = np.linalg.norm(m.predict(xp[None, :])[0] - tgt)
    check("제안이 목표에 가까워짐", d1 < d0, f"{d0:.2f} → {d1:.2f}")

    # ---- 방향성 부호
    d = m.direction(0)
    check("방향성 부호가 참값과 일치", d["a"] > 0 and d["b"] < 0,
          f"a={d['a']:.2f} b={d['b']:.2f}")

    # ---- 반응 공분산 (역할 2 의 자리)
    check("반응 공분산이 양정치", np.all(np.linalg.eigvalsh(m.Sigma) > 0))
    check("반응 상관을 실제로 씀 (마할라노비스)",
          "Sigma_inv" in open(MIXTURE_SRC, encoding="utf-8").read())

    # ---- 예측 불확실성
    mu, var = m.predict(np.vstack([x0, m.to_full(np.full((1, 4), 14.0))[0]]),
                        with_var=True)
    check("외삽 지점의 분산이 더 큼", bool((var[1] > var[0]).all()),
          f"{np.sqrt(var[0]).round(2)} vs {np.sqrt(var[1]).round(2)}")

    # ---- 데이터 0 건에서 첫 제안 (닭·달걀을 푸는 경로)
    # Gt 는 합성 데이터를 만들 때 쓴 계수라 이미 원단위다 → zsd="unit"
    m0 = MixtureModel(names, filler="water", total=T).fit_prior_only(
        prior=Gt, prior_precision=np.full(4, 2.0), zsd="unit")
    xp0 = propose(m0, tgt, x0)
    check("데이터 0 건에서도 제안이 나옴", abs(xp0.sum() - T) < 1e-6, f"{xp0.sum():.4f}")

    # ---- 혼합물이 아닌 데이터는 거부
    try:
        MixtureModel(names, filler="water", total=T).fit(X * 0.8, Y)
        check("합계가 틀린 데이터를 거부함", False, "받아들여 버렸다")
    except ValueError:
        check("합계가 틀린 데이터를 거부함", True)

    # ---------------------------------------------------------- 옛 이름 경로
    # run_propose.py 등이 부르는 이름이 새 수학으로 이어져 있는지.
    # 이름만 남기고 속을 갈았으므로, 여기가 끊기면 옛 결과가 조용히 되살아난다.
    snames = ["s1", "s2"]
    PRIOR = {"s1": {"a": (3, "medium"), "b": (-2, "medium")},
             "s2": {"b": (2, "high")}}
    pred = P.SensoryPredictor(names).fit(X, Y, snames, PRIOR)
    check("필러를 자동으로 찾음", pred.filler == "water", pred.filler)
    check("총량을 자동으로 찾음", abs(pred.total - T) < 1e-6, str(pred.total))

    lo, hi = X.min(0), X.max(0)
    xq = P.propose_recipe(pred, tgt, lo, hi, x0)
    check("옛 이름 propose_recipe 도 합계를 지킴", abs(xq.sum() - T) < 1e-6,
          f"{xq.sum():.4f}")
    xr = P.parsimony_trim(pred, xq, lo, hi, tgt)
    check("옛 이름 parsimony_trim 도 합계를 지킴", abs(xr.sum() - T) < 1e-6,
          f"{xr.sum():.4f}")

    # 필러 열의 기울기는 0 이어야 한다 — 잔량이므로 자유변수가 아니다
    B = pred.B
    check("필러 열의 기울기가 0", np.allclose(B[:, names.index("water")], 0.0))

    # ---- 절편 식별 문제를 다시 만들지 않았는지
    Zc = m.to_free(X)
    M = np.column_stack([np.ones(len(X)), Zc])
    check("자유 좌표에서는 절편이 식별됨",
          np.linalg.matrix_rank(M) == M.shape[1],
          f"열 {M.shape[1]} · rank {np.linalg.matrix_rank(M)}")
    Mfull = np.column_stack([np.ones(len(X)), X])
    check("전체 좌표는 여전히 공선임을 확인 (그래서 자유 좌표를 쓴다)",
          np.linalg.matrix_rank(Mfull) < Mfull.shape[1],
          f"열 {Mfull.shape[1]} · rank {np.linalg.matrix_rank(Mfull)}")

    # ---------------------------------------------------------- 출력
    print("=" * 62)
    print("  remi 모델 자체 점검")
    print("=" * 62)
    for n, _ in OK:
        print(f"  통과  {n}")
    for n, d in BAD:
        print(f"  실패  {n}   {d}")
    print("=" * 62)
    print(f"  {len(OK)}건 통과" + (f" · {len(BAD)}건 실패" if BAD else " · 전부 통과"))
    print("=" * 62)
    return 1 if BAD else 0


if __name__ == "__main__":
    sys.exit(main())
