# -*- coding: utf-8 -*-
"""
v2 경로 자체 검사 — Layer A 편입 · mixture.py 세 수정 · 어댑터.

selfcheck_model.py 가 v1 수학을 지킨다면, 이 파일은 v2 온톨로지에서
모형까지 오는 길을 지킨다. 각 검사는 실제로 났던 오류 하나에 대응한다.

    python selfcheck_v2.py
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from formulator.mixture import MixtureModel, _as_lambda        # noqa: E402
from formulator.v2adapter import V2Ontology, DEMO_ICECREAM     # noqa: E402

_n_pass = 0
_n_fail = 0


def check(label, ok, detail=""):
    global _n_pass, _n_fail
    if ok:
        _n_pass += 1
        print(f"  통과  {label}" + (f"   ({detail})" if detail else ""))
    else:
        _n_fail += 1
        print(f"  실패  {label}" + (f"   ({detail})" if detail else ""))


def raises(fn, *a, **kw):
    """(예외가 났는가, 메시지)"""
    try:
        fn(*a, **kw)
        return False, ""
    except Exception as e:                                   # noqa: BLE001
        return True, str(e)


print("=" * 62)
print("  remi v2 경로 자체 검사")
print("=" * 62)

# ---------------------------------------------------------------- B1 스케일
print("\n[B1] 사전계수 스케일")

names = ["a", "b", "c", "water"]
G = np.array([[1.0], [0.5], [-0.3]])

m = MixtureModel(names, filler="water", total=100.0)
ok, msg = raises(m.fit_prior_only, prior=G)
check("zsd 없이 부르면 거부한다", ok and "zsd" in msg,
      "예전에는 조용히 1 로 두어 1pp 를 1SD 로 읽었다")

m = MixtureModel(names, filler="water", total=100.0)
m.fit_prior_only(prior=G, zsd="unit")
check('zsd="unit" 로 원단위를 명시할 수 있다', m.fitted and np.allclose(m.zsd, 1.0))

m2 = MixtureModel(names, filler="water", total=100.0)
ok, msg = raises(m2.fit_prior_only, prior=G, zsd="raw")
check("zsd 문자열은 unit 만 받는다", ok)

m3 = MixtureModel(names, filler="water", total=100.0)
ok, _ = raises(m3.fit_prior_only, prior=G, zsd=[1.0, -2.0, 1.0])
check("zsd 에 0 이하가 있으면 거부한다", ok)

# 스케일이 실제로 예측을 척도 안에 잡아두는가
m4 = MixtureModel(names, filler="water", total=100.0)
m4.fit_prior_only(prior=G, zsd=[3.0, 3.0, 3.0], zbar=[6.0, 6.0, 6.0])
x = np.array([12.0, 6.0, 6.0, 76.0])
y = m4.predict(x[None, :])[0]
check("작업 범위 기반 스케일에서 예측이 ±3 안에 머문다",
      abs(y[0]) <= 3.0, f"{y[0]:+.2f}")

m5 = MixtureModel(names, filler="water", total=100.0)
m5.fit_prior_only(prior=G, zsd="unit")
y_raw = m5.predict(x[None, :])[0]
check("원단위 해석은 같은 배합에서 척도를 벗어난다(예전 동작)",
      abs(y_raw[0]) > 3.0, f"{y_raw[0]:+.2f} ← 이것이 +20 을 만든 경로")

# ---------------------------------------------------------------- B3 행 수
print("\n[B3] Γ₀ 행 수 검증")

m6 = MixtureModel(names, filler="water", total=100.0)
G_full = np.array([[1.0], [0.5], [-0.3], [0.0]])          # 필러 행까지 4행
ok, msg = raises(m6.fit_prior_only, prior=G_full, zsd="unit")
check("팔레트 전체 행수(필러 포함)를 거부한다", ok and "자유변수" in msg)
check("오류 메시지가 필러를 빼라고 알려준다", ok and "필러" in msg,
      "예전에는 propose() 안에서 broadcast 오류로 터졌다")

m7 = MixtureModel(names, filler="water", total=100.0)
ok, _ = raises(m7.fit_prior_only, prior=np.array([1.0, 0.5, -0.3]), zsd="unit")
check("1차원 prior 를 거부한다", ok)

# ---------------------------------------------------------------- B4 Λ
print("\n[B4] 엣지별 확신도 Λ")

lam1 = _as_lambda(np.array([8.0, 2.0, 0.4]), 3, 2)
check("(q,) Λ 는 모든 반응으로 넓혀진다", lam1.shape == (3, 2)
      and np.allclose(lam1[:, 0], lam1[:, 1]))

lam2 = _as_lambda(np.array([[8.0, 0.4], [2.0, 2.0], [0.4, 8.0]]), 3, 2)
check("(q,m) Λ 를 그대로 받는다", lam2.shape == (3, 2) and lam2[0, 0] == 8.0)

ok, _ = raises(_as_lambda, np.array([1.0, 2.0]), 3, 2)
check("길이가 안 맞는 Λ 를 거부한다", ok)

# 열마다 다른 Λ 가 실제로 다른 추정을 내는가
G0 = np.array([[1.0, 1.0], [1.0, 1.0], [1.0, 1.0]])
mA = MixtureModel(names, filler="water", total=100.0)
mA.fit_prior_only(prior=G0, prior_precision=lam2, zsd="unit")
check("Λ 가 (m,q,q) Ainv 로 반영된다", mA.Ainv.shape == (2, 3, 3))
check("확신도가 높은 엣지일수록 사후 분산이 작다",
      mA.Ainv[0][0, 0] < mA.Ainv[1][0, 0],
      f"Λ=8 → {mA.Ainv[0][0,0]:.3f} vs Λ=0.4 → {mA.Ainv[1][0,0]:.3f}")

# 데이터가 있을 때도 열별로 풀리는가
rng = np.random.default_rng(0)
Z = rng.uniform(2, 10, size=(12, 3))
X = np.column_stack([Z, 100.0 - Z.sum(1)])
Y = Z @ np.array([[1.0, -1.0], [0.2, 0.6], [-0.5, 0.1]]) + rng.normal(0, .05, (12, 2))
mB = MixtureModel(names, filler="water", total=100.0).fit(
    X, Y, prior=G0, prior_precision=lam2)
check("fit() 도 (q,m) Λ 를 받는다", mB.G.shape == (3, 2) and mB.Ainv.shape == (2, 3, 3))
mC = MixtureModel(names, filler="water", total=100.0).fit(X, Y, ridge=1.0)
check("Λ 가 다르면 추정도 달라진다(뭉개지지 않는다)",
      not np.allclose(mB.G, mC.G))
mu, var = mB.predict(X[:3], with_var=True)
check("예측 분산이 반응마다 따로 나온다", var.shape == (3, 2)
      and not np.allclose(var[:, 0], var[:, 1]))

# ---------------------------------------------------------------- Layer A
print("\n[Layer A] 정본 편입")

import yaml                                                   # noqa: E402

onto = V2Ontology()
apath = os.path.join(onto.layers, "layerA_parameters.yaml")
check("layerA_parameters.yaml 이 v2 layers/ 에 있다", os.path.exists(apath))
A = yaml.safe_load(open(apath, encoding="utf-8"))
P = {p["id"]: p for p in A["parameters"]}
check("파라미터 38종(스펙 37 + 신규 1)", len(P) == 38, f"{len(P)}")
check("unit 누락 없음", all("unit" in p for p in P.values()))
check("P.shear_thinning_index 정의됨", "P.shear_thinning_index" in P)

refs = set(r["parameter"] for r in onto.stack["R"]["relations_proxy"])
for sp in onto.stack["S"]:
    for p in (sp.get("parameters") or []):
        refs.add(p["id"])
for t in onto.tags.values():
    for e in (t.get("effects") or []):
        if str(e.get("to", "")).startswith("P."):
            refs.add(e["to"])
for g in onto.ingredients.values():
    for e in (g.get("overrides") or []):
        if str(e.get("to", "")).startswith("P."):
            refs.add(e["to"])
dangling = sorted(r for r in refs if r not in P)
check("매달린 P.* 참조 없음", not dangling, str(dangling))

# ---------------------------------------------------------------- 어댑터
print("\n[어댑터] v2 → MixtureModel")

check("온톨로지 로드", len(onto.ingredients) > 100 and len(onto.tags) > 20,
      f"재료 {len(onto.ingredients)} · 태그 {len(onto.tags)}")
check("프로파일 5종 모두 필러를 찾는다",
      all(onto.filler_of(p) for p in onto.profiles))

built = onto.build("icecream", list(DEMO_ICECREAM), bounds=DEMO_ICECREAM)
q_free = len(DEMO_ICECREAM)
check("필러 행이 제거된다", built.Gamma0.shape[0] == q_free,
      f"Γ₀ {built.Gamma0.shape}")
check("Λ 가 (q,m) 로 전달된다", built.Lambda.shape == built.Gamma0.shape)
check("Λ 의 확신도 구분이 살아 있다",
      len(set(np.round(built.Lambda[built.Gamma0 != 0], 2).tolist())) > 1,
      f"{sorted(set(np.round(built.Lambda[built.Gamma0 != 0],2).tolist()))}")
check("범위를 주면 G5 경고가 사라진다",
      not any("작업 범위가 없어" in w for w in built.warnings))

b2 = onto.build("icecream", list(DEMO_ICECREAM))          # 범위 없이
check("범위가 없으면 경고를 남긴다",
      any("작업 범위가 없어" in w for w in b2.warnings))

x0 = np.zeros(len(built.palette))
for i, g in enumerate([n for n in built.palette if n != built.filler]):
    x0[built.palette.index(g)] = built.zbar[i]
x0[built.palette.index(built.filler)] = 100.0 - x0.sum()
check("범위 중앙값 배합의 합계가 100", abs(x0.sum() - 100.0) < 1e-9)

x = onto.suggest(built, {"L.tx.creaminess": 1.0}, x0=x0, bounds=DEMO_ICECREAM)
check("제안의 합계가 100", abs(x.sum() - 100.0) < 1e-6, f"{x.sum():.6f}")

free = [n for n in built.palette if n != built.filler]
within = all(DEMO_ICECREAM[g][0] - 1e-6 <= x[built.palette.index(g)]
             <= DEMO_ICECREAM[g][1] + 1e-6 for g in free)
check("제안이 작업 범위 안에 머문다(G5 경계 적용)", within)

y = built.model.predict(x[None, :])[0]
check("예측이 ±3 관능 척도 안", np.abs(y).max() <= 3.0, f"최대 {np.abs(y).max():.2f}")

i_cr = built.y_terms.index("L.tx.creaminess")
y0 = built.model.predict(x0[None, :])[0]
check("크리미니스 목표에 실제로 가까워진다",
      abs(y[i_cr] - 1.0) < abs(y0[i_cr] - 1.0),
      f"{y0[i_cr]:+.2f} → {y[i_cr]:+.2f} (목표 +1.0)")

fat = x[built.palette.index("ING.refined_coconut_oil")]
fat0 = x0[built.palette.index("ING.refined_coconut_oil")]
check("크리미니스를 올리려 지방을 늘린다(방향이 식품과학과 맞음)",
      fat > fat0, f"{fat0:.2f} → {fat:.2f}")

ok, msg = raises(onto.suggest, built, {"L.tx.nonexistent": 1.0})
check("모르는 축을 목표로 주면 거부한다", ok)


# ---------------------------------------------------------------- 온톨로지 감사
print("")
print("[감사] 스펙이 요구하나 정본 로더가 안 하는 검사")

# 의도적으로 효과가 없는 재료 — 이유가 문서화된 것만 허용한다
ALLOWED_INERT = {
    "ING.plant_extract",      # shortlist 가 효과 없음으로 제외 등급을 매김
    "ING.calcium_lactate",    # 중성염. 역할은 칼슘 공급인데 대응 P 가 없다
    "ING.potassium_sorbate",  # 보존제. 관능/물성 축이 아니다
}

aud = onto.audit()

check("direction 없는 엣지가 없다", not aud["directionless"],
      f"{len(aud['directionless'])}건 — 있으면 로더가 조용히 0 으로 만든다")
for _k, _o, _t, _s in aud["directionless"][:5]:
    print(f"        {_k} {_o} -> {_t}")

_inert = [g for g in aud["untagged"] if g not in ALLOWED_INERT]
check("효과를 하나도 못 내는 재료가 없다", not _inert, str(_inert))

# 검토에서 '보류' 로 판정해 일부러 엣지를 뺀 재료. 결함이 아니라 결정이다.
# 보류 사유가 문서에 남아 있는 것만 여기 넣는다.
HELD_PENDING_REVIEW = {
    # 2026-08-31 검토: "'신선한' 향이라는 정의 자체가 불분명하다. 영어 fresh 와
    # 한글 '신선한' 은 느낌이 다르다" -> 용어 정의 확정 전까지 향 엣지 보류.
    # ontology_v2/기름_관능용어_정리.md 3절 참조.
    "ING.chili_fresh_red",
}
_unful = [x for x in aud["unfulfilled"] if x[0] not in HELD_PENDING_REVIEW]
_held = [x for x in aud["unfulfilled"] if x[0] in HELD_PENDING_REVIEW]
check("향미재가 모두 향 축을 움직인다", not _unful,
      f"{len(_unful)}건" + (f" · 보류 {len(_held)}건 제외" if _held else ""))
for _g, _t, _w in _held:
    print(f"        보류  {_g}: {_w} (검토 결정)")
for _g, _t, _w in _unful[:5]:
    print(f"        {_g}: {_w}")

check("어떤 재료로도 못 움직이는 core 축이 없다", not aud["dead_core"],
      str(aud["dead_core"]))

# 스펙 5.9 — 액추에이터 없는 R-1 은 플래그 대상이지 실패는 아니다.
# 없는 파라미터를 지어내는 것보다 보이게 두는 편이 낫다.
_n_orphan = sum(len(v) for v in aud["orphan_proxies"].values())
print(f"  참고  액추에이터 없는 R-1 {_n_orphan}건 (스펙 5.9 플래그)")
for _p, _xs in aud["orphan_proxies"].items():
    print(f"        [{_p}] {chr(44).join(_xs)}")
print("\n" + "=" * 62)
print(f"  {_n_pass}건 통과 · {_n_fail}건 실패")
print("=" * 62)
sys.exit(1 if _n_fail else 0)
