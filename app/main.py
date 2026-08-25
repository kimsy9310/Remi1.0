# -*- coding: utf-8 -*-
"""
Remi 1.0 — 웜루프 앱

    실측 데이터 → 사전값 보정 → 다음 실험 제안 → (랩) → 다시 실측

실행:  streamlit run app/main.py
"""
from __future__ import annotations

import os
import sys

import numpy as np
import streamlit as st

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for p in (os.path.join(_ROOT, "engine"), _HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

import dataio                                    # noqa: E402
import palette as pal                            # noqa: E402
import store                                     # noqa: E402
import warmloop as wl                            # noqa: E402
from formulator.v2adapter import V2Ontology      # noqa: E402

st.set_page_config(page_title="Remi 1.0", page_icon="🧪", layout="wide")

DATA_DIR = os.path.join(_ROOT, "data")


# ---------------------------------------------------------------- 캐시
@st.cache_resource(show_spinner="온톨로지 로드 중…")
def get_onto():
    return V2Ontology()


@st.cache_data(show_spinner="실측 데이터 읽는 중…")
def get_data(path, profile, _mtime):
    return dataio.load_warmloop(path, get_onto(), profile)


@st.cache_data(show_spinner=False)
def get_palette(profile, _mtime):
    return pal.load(profile)


def load_palette(profile):
    """팔레트 표. 없거나 이 프로파일 행이 없으면 None 을 준다(앱은 계속 돈다)."""
    try:
        t = get_palette(profile, os.path.getmtime(pal.DEFAULT_PATH))
        return t if t.rows else None
    except FileNotFoundError:
        return None
    except Exception as e:                                        # noqa: BLE001
        st.sidebar.error(f"팔레트 표를 읽지 못했습니다: {e}")
        return None


def core_terms(profile):
    cards = onto._ref.load_cards(profile, onto.layers)
    return [c["term_id"] for c in cards
            if c["tier"] == "core" and c["evidence_required"] != "sample_aged"]


def axis_label(t):
    return t.split(".")[-1]


def ing_label(g):
    return g.replace("ING.", "")


# ---------------------------------------------------------------- 사이드바
onto = get_onto()

st.sidebar.title("Remi 1.0")
st.sidebar.caption("식품 레시피 포뮬레이터 · 웜루프")

profiles = sorted(onto.profiles)
default_ix = profiles.index("beverage_rice_milk") if "beverage_rice_milk" in profiles else 0
profile = st.sidebar.selectbox("프로파일", profiles, index=default_ix)

xlsx = sorted(f for f in os.listdir(DATA_DIR) if f.endswith(".xlsx") and not f.startswith("~"))
if not xlsx:
    st.sidebar.error("data/ 에 xlsx 가 없습니다.")
    st.stop()
fname = st.sidebar.selectbox("실측 데이터", xlsx)
fpath = os.path.join(DATA_DIR, fname)

st.sidebar.divider()
st.sidebar.caption(
    f"온톨로지 재료 {len(onto.ingredients)}종 · 태그 {len(onto.tags)}종\n\n"
    f"필러 `{onto.filler_of(profile)}`")

# ---------------------------------------------------------------- 데이터 로드
try:
    data = get_data(fpath, profile, os.path.getmtime(fpath))
except Exception as e:                                            # noqa: BLE001
    st.error(f"**데이터를 읽지 못했습니다**\n\n{e}")
    st.info(
        "이 프로파일의 M 카드에 `legacy_column` 이 있어야 관능 컬럼이 L.* 축과 이어집니다. "
        "`ontology_v2/layers/layerM_cards_*.yaml` 을 확인하세요.")
    st.stop()

tab_data, tab_learn, tab_suggest, tab_bounds = st.tabs(
    ["① 데이터", "② 학습", "③ 제안", "④ 팔레트"])

# ================================================================= ① 데이터
with tab_data:
    st.subheader("무엇이 들어왔나")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("샘플", len(data.sample_ids))
    c2.metric("재료", len(data.names))
    c3.metric("관능 축", len(data.y_terms))
    c4.metric("벤치마크", len(data.benchmark_ids) or "—")

    for n in data.notes:
        st.warning(n, icon="⚠️")
    if data.unmapped_columns:
        st.warning(f"온톨로지 ID 로 잇지 못한 컬럼: {data.unmapped_columns}", icon="⚠️")
    if data.missing_axes:
        st.info(f"카드는 있으나 데이터에 컬럼이 없는 축: "
                f"{[axis_label(t) for t in data.missing_axes]}")

    st.markdown("##### 관능 (벤치마크 상대, −3…+3)")
    st.dataframe(
        {"sample": data.sample_ids,
         **{axis_label(t): data.Y[:, k].tolist() for k, t in enumerate(data.y_terms)}},
        use_container_width=True, hide_index=True)

    with st.expander("배합 (합계 100으로 정규화)"):
        st.caption(f"원본 배치 합계: {np.round(data.raw_totals, 1).tolist()}")
        st.dataframe(
            {"sample": data.sample_ids,
             **{ing_label(g): np.round(data.X[:, i], 3).tolist()
                for i, g in enumerate(data.names)}},
            use_container_width=True, hide_index=True)

# ================================================================= ② 학습
with tab_learn:
    st.subheader("사전값을 실측이 얼마나 밀어냈나")
    ptab = load_palette(profile)
    bounds = ptab.bounds() if ptab else {}
    try:
        res = wl.run(onto, data, profile, bounds=bounds or None)
    except Exception as e:                                        # noqa: BLE001
        st.error(f"적합에 실패했습니다: {e}")
        st.stop()

    c1, c2, c3 = st.columns(3)
    c1.metric("적합에 쓴 샘플", res.n)
    c2.metric("탐색된 독립 방향", res.eff_directions,
              delta=f"자유변수 {len(res.free)}개 중",
              delta_color="off")
    c3.metric("부호가 뒤집힌 칸", len(res.contradicted()))

    if res.eff_directions < len(res.free):
        st.info(
            f"샘플은 {res.n}건이지만 실제로 탐색된 독립 방향은 **{res.eff_directions}개**입니다. "
            f"재료를 함께 움직이면 여러 런이 같은 방향을 반복합니다 — "
            f"개수보다 정보량이 중요한 이유입니다.", icon="📐")
    for w in res.warnings:
        st.warning(w, icon="⚠️")

    st.markdown("##### 가장 많이 움직인 칸")
    sh = res.shifts(20)
    if sh:
        st.dataframe(
            {"재료": [ing_label(s["ingredient"]) for s in sh],
             "축": [axis_label(s["axis"]) for s in sh],
             "사전": [round(s["prior"], 2) for s in sh],
             "실측 보정": [round(s["post"], 2) for s in sh],
             "이동": [round(s["shift"], 2) for s in sh],
             "Λ(확신도)": [s["lam"] for s in sh],
             "부호뒤집힘": ["예" if s["flipped"] else "" for s in sh]},
            use_container_width=True, hide_index=True)

    cc = res.contradicted()
    if cc:
        st.markdown("##### 온톨로지와 부호가 반대인 칸")
        st.caption(
            "사전지식이 틀렸을 수도, 실험이 교락됐을 수도 있습니다. Λ 가 낮고 이동이 작으면 "
            "약한 증거이니 성급히 온톨로지를 고치지 마세요.")
        for s in cc:
            st.write(
                f"- **{ing_label(s['ingredient'])}** → *{axis_label(s['axis'])}* : "
                f"사전 `{s['prior']:+.2f}` / 실측 `{s['post']:+.2f}`  (Λ={s['lam']})")

    ls = res.learned_from_silence()
    if ls:
        with st.expander(f"사전이 비어 있던 칸을 데이터가 채운 것 ({len(ls)}개)"):
            st.caption("온톨로지에 엣지가 없던 자리입니다. 반복해서 확인되면 온톨로지에 "
                       "추가할 후보입니다.")
            st.dataframe(
                {"재료": [ing_label(s["ingredient"]) for s in ls],
                 "축": [axis_label(s["axis"]) for s in ls],
                 "실측 계수": [round(s["post"], 2) for s in ls]},
                use_container_width=True, hide_index=True)

    st.session_state["res"] = res

# ================================================================= ③ 제안
with tab_suggest:
    st.subheader("다음 실험 제안")
    res = st.session_state.get("res")
    if res is None:
        st.info("먼저 ② 학습 탭을 여세요.")
        st.stop()

    ptab = load_palette(profile)
    bounds = ptab.bounds() if ptab else {}
    if not bounds:
        st.warning(
            "재료 범위가 하나도 없습니다. 상한 없이 제안하면 물리적으로 불가능한 배합이 "
            "나올 수 있습니다. **④ 팔레트** 탭에서 먼저 넣어주세요.", icon="🚧")
    elif ptab:
        miss = [g for g in res.free if g not in bounds]
        if miss:
            st.info(
                f"범위가 없는 재료 {len(miss)}종은 경계 없이 움직입니다: "
                f"{[ing_label(g) for g in miss[:8]]}", icon="ℹ️")

    base_ix = st.selectbox(
        "기준 배합", range(len(res_ids := data.sample_ids)),
        format_func=lambda i: res_ids[i],
        index=len(res_ids) - 1,
        help="여기서 출발해 목표 쪽으로 움직입니다.")
    order = [data.names.index(g) for g in res.names]
    x0 = data.X[base_ix][order]

    st.markdown("##### 목표 (0 = 유지)")
    cols = st.columns(len(res.y_terms))
    target = {}
    for c, t in zip(cols, res.y_terms):
        target[t] = c.slider(axis_label(t), -3.0, 3.0, 0.0, 0.25, key=f"tg_{t}")

    if st.button("제안 만들기", type="primary"):
        try:
            x = wl.suggest(res, target, x0, bounds=bounds or None)
        except Exception as e:                                    # noqa: BLE001
            st.error(f"제안에 실패했습니다: {e}")
            st.stop()

        delta = x - x0
        st.markdown("##### 배합 변경")
        st.dataframe(
            {"재료": [ing_label(g) for g in res.names],
             "기준": np.round(x0, 3).tolist(),
             "제안": np.round(x, 3).tolist(),
             "변화": [f"{d:+.3f}" if abs(d) > 1e-4 else "" for d in delta]},
            use_container_width=True, hide_index=True)
        st.caption(f"합계 {x.sum():.4f}")

        y0 = res.model.predict(x0[None, :])[0]
        y1 = res.model.predict(x[None, :])[0]
        st.markdown("##### 예측 관능")
        st.dataframe(
            {"축": [axis_label(t) for t in res.y_terms],
             "목표": [target[t] for t in res.y_terms],
             "기준 예측": np.round(y0, 2).tolist(),
             "제안 예측": np.round(y1, 2).tolist()},
            use_container_width=True, hide_index=True)

        if np.abs(y1).max() > 3.0:
            st.error(
                f"예측이 ±3 관능 척도를 벗어났습니다(최대 {np.abs(y1).max():.1f}). "
                f"재료 범위가 없거나 너무 넓을 때 생깁니다.", icon="🚨")

        store.log_run(profile, fname, res.n, res.y_terms,
                      target={axis_label(k): v for k, v in target.items()},
                      proposal={ing_label(g): round(float(v), 4)
                                for g, v in zip(res.names, x)})
        st.success("제안을 이력에 저장했습니다.")

    hist = store.recent_runs(5)
    if hist:
        with st.expander("최근 제안 이력"):
            for r in hist:
                st.write(f"`{r[1]}` · {r[2]} · 샘플 {r[3]}건 · 목표 {r[4]}")


# ================================================================= ④ 팔레트
with tab_bounds:
    st.subheader("팔레트와 작업 범위")
    ptab = load_palette(profile)

    if ptab is None:
        st.error(
            "이 프로파일의 팔레트 행이 없습니다.\n\n"
            "`python tools/build_palette.py` 로 표를 만들거나, "
            "`data/palette.xlsx` 에 이 프로파일 행을 추가하세요.")
        st.stop()

    stt = ptab.status()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("쓸 수 있는 재료", stt["usable"])
    c2.metric("범위 입력됨", stt["with_range"],
              delta=f"-{stt['missing']}종 남음" if stt["missing"] else "완료",
              delta_color="inverse" if stt["missing"] else "normal")
    c3.metric("제외 등급", stt["excluded"])
    c4.metric("확인 필요", stt["flagged"])

    st.progress(stt["with_range"] / max(stt["usable"], 1),
                text=f"범위 {stt['with_range']} / {stt['usable']}")
    st.caption(
        "온톨로지의 `limitations` 는 자유 서술이라 기계가 읽지 못합니다(스펙 G5). "
        "여기 값이 제안의 상·하한이자 사전계수의 스케일이 됩니다. "
        "**채워질수록 제안 숫자를 믿을 수 있습니다.** 원본은 `data/palette.xlsx`.")

    # ---- 목표축 커버리지 (G2)
    core = core_terms(profile)
    cov = ptab.coverage(core)
    dead = [t for t, v in cov.items() if not v]
    st.markdown("##### 목표축 커버리지")
    st.dataframe(
        {"목표축": [axis_label(t) for t in core],
         "이 축을 움직이는 재료": [len(cov[t]) for t in core],
         "예": [", ".join(ing_label(g) for g in cov[t][:4]) or "— 없음" for t in core]},
        use_container_width=True, hide_index=True)
    if dead:
        st.error(
            f"움직일 수 있는 재료가 없는 축: **{[axis_label(t) for t in dead]}** — "
            f"목표로 줘도 반응하지 않습니다. 해당 축을 움직이는 재료를 팔레트에 넣거나, "
            f"온톨로지에 엣지가 없는 경우입니다.", icon="🚨")

    na = ptab.no_axis()
    if na:
        st.warning(
            f"이 프로파일에서 아무 목표축도 못 움직이는 재료 {len(na)}종: "
            f"{[ing_label(g) for g in na]} — 배합에는 넣을 수 있지만 모형은 조종 수단으로 "
            f"쓰지 못합니다.", icon="⚠️")
    fl = ptab.flagged()
    if fl:
        with st.expander(f"확인 필요 {len(fl)}건"):
            for g, why in fl:
                st.write(f"- `{ing_label(g)}` — {why}")
    bad = ptab.bad_ranges()
    if bad:
        st.error(f"상한이 하한보다 작거나 같은 행: {bad}", icon="🚨")

    # ---- 편집
    st.markdown("##### 표 편집")
    st.caption("하한·상한을 채우고 저장하면 `data/palette.xlsx` 에 바로 반영됩니다.")

    order = {g: i for i, g in enumerate(["필수", "권장", "옵션", "제한", "제외"])}
    rows = sorted(ptab.rows,
                  key=lambda r: (order.get(r["등급"], 9), r["슬롯"], r["온톨로지ID"]))
    edited = st.data_editor(
        [{"슬롯": r["슬롯"], "재료": r["재료"], "온톨로지ID": r["온톨로지ID"],
          "등급": r["등급"], "하한": r["하한"], "상한": r["상한"],
          "범위근거": r["범위근거"], "담당축": r["담당축"],
          "메모": r["메모"], "확인": r["확인"]} for r in rows],
        use_container_width=True, hide_index=True, num_rows="fixed",
        column_config={
            "등급": st.column_config.SelectboxColumn(
                options=["필수", "권장", "옵션", "제한", "제외"], width="small"),
            "하한": st.column_config.NumberColumn(min_value=0.0, step=0.05, format="%.3f"),
            "상한": st.column_config.NumberColumn(min_value=0.0, step=0.05, format="%.3f"),
            "온톨로지ID": st.column_config.TextColumn(disabled=True),
            "담당축": st.column_config.TextColumn(disabled=True, help="온톨로지가 계산합니다"),
        },
        key=f"pal_{profile}")

    if st.button("저장", type="primary"):
        out, bad2 = [], []
        for e in edited:
            lo, hi = e.get("하한"), e.get("상한")
            if lo is not None and hi is not None and hi <= lo:
                bad2.append(f"{ing_label(e['온톨로지ID'])}: 상한({hi}) ≤ 하한({lo})")
                continue
            out.append({"프로파일": profile, "슬롯": e["슬롯"], "재료": e["재료"],
                        "온톨로지ID": e["온톨로지ID"], "등급": e["등급"],
                        "하한": lo, "상한": hi, "범위근거": e["범위근거"],
                        "담당축": e["담당축"], "메모": e["메모"], "확인": e["확인"]})
        if bad2:
            for b in bad2:
                st.error(b)
        else:
            pal.save_rows(profile, out)
            st.cache_data.clear()
            st.success(f"{len(out)}행을 저장했습니다.")
            st.rerun()

    with st.expander("슬롯 구성"):
        st.caption(
            "슬롯 하나가 모형의 변수 하나입니다. 같은 슬롯에 재료가 여럿이면 "
            "각각을 독립 변수로 두지 말고 총량+비율로 묶는 편이 낫습니다 — "
            "죽은 코너가 사라지고 런이 낭비되지 않습니다.")
        for slot, gs in ptab.slots().items():
            st.write(f"**{slot}** ({len(gs)}) — {', '.join(ing_label(g) for g in gs)}")
