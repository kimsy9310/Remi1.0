# -*- coding: utf-8 -*-
"""
사용자 화면 — 단계형 인터뷰.

    ① 무엇을 만드시나요      제형/제품 고르기 + 기준 제품 적기
    ② 어떻게 바꾸고 싶나요    core 축마다 "기준보다 더/덜"
    ③ 무엇을 쓰시나요        슬롯별 재료 고르기
    ④ 배합 제안             엔진이 낸 배합과 그 근거

전문가 화면(데이터·학습·팔레트)은 따로 둔다. 여기서는 만들 사람이 답할 수 있는
것만 묻는다.

질문은 전부 온톨로지에서 생성한다 — interview.py 참조.
"""
from __future__ import annotations

import numpy as np
import streamlit as st

import interview as iq


STEPS = ["① 무엇을 만드시나요", "② 어떻게 바꾸고 싶나요", "③ 무엇을 쓰시나요", "④ 배합 제안"]


def _iv():
    if "iv" not in st.session_state:
        st.session_state.iv = iq.Interview()
    return st.session_state.iv


def _goto(i):
    st.session_state.step = max(0, min(i, len(STEPS) - 1))


def render(onto, load_palette, build_model, propose_fn):
    """
    onto         : V2Ontology
    load_palette : (profile, variant) -> PaletteTable | None
    build_model  : (profile, palette, bounds, variant) -> BuiltModel
    propose_fn   : (built, target, x0, bounds, free_axes) -> ndarray
    """
    iv = _iv()
    step = st.session_state.setdefault("step", 0)

    # ---- 진행 표시
    cols = st.columns(len(STEPS))
    for i, (c, name) in enumerate(zip(cols, STEPS)):
        done = i < step
        now = i == step
        c.markdown(
            f"{'**' if now else ''}{name}{'**' if now else ''}"
            + ("  ✓" if done else ""))
    st.progress((step + 1) / len(STEPS))
    st.divider()

    # ================================================== ① 무엇을 만드나
    if step == 0:
        st.subheader("무엇을 만드시나요?")
        choices = iq.product_choices(onto, load_palette)
        labels = [
            c["label"]
            + ("  (제품)" if c["is_product"] else "")
            + ("" if c["ready"] else "  — 재료 표 없음")
            for c in choices]
        idx = 0
        if iv.profile:
            for i, c in enumerate(choices):
                if c["profile"] == iv.profile:
                    idx = i
        pick = st.radio("제품 종류", range(len(choices)),
                        format_func=lambda i: labels[i], index=idx)
        ch = choices[pick]
        st.caption(ch["definition"])
        if ch["boundary"]:
            st.caption(f"경계: {ch['boundary']}")

        vars_ = _variants(onto, ch["profile"])
        variant = None
        if vars_:
            v = st.selectbox("목적", ["(기본)"] + vars_,
                             help="같은 제형이라도 목적에 따라 재료 범위가 달라집니다.")
            variant = None if v == "(기본)" else v

        st.markdown("##### 기준으로 삼을 제품")
        st.caption(
            "이 도구는 **기준 대비 얼마나 다른가**로 맛을 다룹니다. 잘 아는 제품을 "
            "하나 정해 두면 다음 질문이 '그것보다 더/덜'이 되어 답하기 쉬워집니다.")
        bm = st.text_input("예: 시중 ○○ 제품, 지난 시제품 3번",
                           value=iv.benchmark, placeholder="이름만 적어두셔도 됩니다")

        if not ch["ready"]:
            st.warning(
                "이 제품은 아직 쓸 재료 표가 없습니다. 전문가 화면 ④ 팔레트에서 "
                "재료와 사용 범위를 정해 두면 여기서 고를 수 있게 됩니다.",
                icon="🚧")

        if st.button("다음", type="primary", disabled=not ch["ready"]):
            if iv.profile != ch["profile"]:
                iv.goals, iv.chosen, iv.free_axes = {}, {}, []   # 제품이 바뀌면 초기화
            iv.profile, iv.variant, iv.benchmark = ch["profile"], variant, bm
            _goto(1)
            st.rerun()

    # ================================================== ② 어떻게 바꾸나
    elif step == 1:
        st.subheader("기준과 비교해 어떻게 바꾸고 싶으세요?")
        if iv.benchmark:
            st.caption(f"기준: **{iv.benchmark}**")
        st.caption("바꾸고 싶지 않은 축은 '기준과 같게'로 두시면 됩니다. "
                   "아예 신경 쓰지 않는 축은 '상관없음'을 켜세요 — "
                   "붙잡아 두면 정작 바꾸려는 축이 눌립니다.")

        qs = iq.goal_questions(onto, iv.profile)
        for q in qs:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"**{q['label']}**")
                free = c2.checkbox("상관없음", key=f"uf_free_{q['term']}",
                                   value=q["term"] in iv.free_axes)
                if q["hint"]:
                    st.caption(q["hint"])
                vals = [o["value"] for o in q["options"]]
                cur = iv.goals.get(q["term"], 0.0)
                sel = st.select_slider(
                    " ", options=vals, value=cur if cur in vals else 0.0,
                    format_func=lambda v, q=q: next(
                        o["label"] for o in q["options"] if o["value"] == v),
                    key=f"uf_goal_{q['term']}", label_visibility="collapsed",
                    disabled=free)
                det = next((o["detail"] for o in q["options"]
                            if o["value"] == sel and o["detail"]), "")
                if det:
                    st.caption(f"→ {det}")
                if q["note"]:
                    with st.expander("이 축을 볼 때 주의할 점"):
                        st.write(q["note"])
                        for p in q["pitfalls"]:
                            st.write(f"- {p}")
                iv.goals[q["term"]] = 0.0 if free else float(sel)
                if free and q["term"] not in iv.free_axes:
                    iv.free_axes.append(q["term"])
                if not free and q["term"] in iv.free_axes:
                    iv.free_axes.remove(q["term"])

        c1, c2 = st.columns(2)
        if c1.button("← 이전"):
            _goto(0); st.rerun()
        if c2.button("다음", type="primary"):
            _goto(2); st.rerun()

    # ================================================== ③ 재료
    elif step == 2:
        st.subheader("무엇을 쓰시나요?")
        ptab = load_palette(iv.profile, iv.variant)
        usable = [r for r in ptab.rows if r["등급"] != "제외"] if ptab else []
        if not usable:
            st.error("이 제품의 재료 표가 비어 있습니다. 전문가 화면 ④ 팔레트에서 "
                     "재료와 사용 범위를 정해 주세요.")
            if st.button("← 이전"):
                _goto(1); st.rerun()
            return
        st.caption("가지고 계신 재료만 고르세요. 고르지 않은 재료는 배합에 쓰이지 않습니다. "
                   "각 재료 옆의 화살표는 그 재료가 무엇을 움직이는지입니다.")

        groups = iq.ingredient_questions(ptab, onto, iv.profile)
        for g in groups:
            head = f"**{g['slot']}**" + ("  · 필수" if g["required"] else "")
            with st.expander(head, expanded=g["required"] or bool(iv.chosen.get(g["slot"]))):
                if g.get("unslotted"):
                    st.caption(
                        "이 제품은 재료 역할이 아직 나뉘어 있지 않아 실측에 쓰인 재료를 "
                        "그대로 보여 드립니다. 전부 켜 둔 상태가 기본입니다.")
                opts = [i["id"] for i in g["items"]]
                lab = {i["id"]: i for i in g["items"]}
                default = iv.chosen.get(g["slot"], g["default"])
                sel = st.multiselect(
                    " ", opts,
                    default=[x for x in default if x in opts],
                    format_func=lambda x: (
                        f"{lab[x]['label']}  [{lab[x]['grade']}]"
                        + (f"  {' '.join(lab[x]['moves'])}" if lab[x]["moves"] else "  (조종 안 됨)")),
                    key=f"uf_ing_{g['slot']}", label_visibility="collapsed")
                iv.chosen[g["slot"]] = sel
                for x in sel:
                    it = lab[x]
                    bits = []
                    if it["bounds"][0] is not None:
                        bits.append(f"범위 {it['bounds'][0]:g}~{it['bounds'][1]:g}%")
                    if it["grade"] == "제한":
                        bits.append("⚠️ 제한 등급 — 목표와 상충할 수 있습니다")
                    if not it["moves"]:
                        bits.append("이 제품에서는 목표축을 움직이지 못합니다")
                    if bits:
                        st.caption(f"· {it['label']}: " + " · ".join(bits))

        st.caption(f"고른 재료 {len(iv.palette())}종")
        c1, c2 = st.columns(2)
        if c1.button("← 이전"):
            _goto(1); st.rerun()
        if c2.button("배합 제안 받기", type="primary", disabled=not iv.palette()):
            _goto(3); st.rerun()

    # ================================================== ④ 제안
    else:
        st.subheader("배합 제안")
        ptab = load_palette(iv.profile, iv.variant)
        msgs = iq.check(onto, iv, ptab)
        for m in msgs:
            st.warning(m, icon="⚠️")

        bounds = ptab.bounds(include_restricted=True) if ptab else {}
        pal = iv.palette()
        try:
            built = build_model(iv.profile, pal, bounds, iv.variant)
        except Exception as e:                                    # noqa: BLE001
            st.error(f"모형을 세우지 못했습니다: {e}")
            if st.button("← 재료 다시 고르기"):
                _goto(2); st.rerun()
            return

        free = [n for n in built.palette if n != built.filler]
        x0 = np.zeros(len(built.palette))
        for i, g in enumerate(free):
            x0[built.palette.index(g)] = built.zbar[i]
        rest = 100.0 - x0.sum()
        if rest < 0:
            st.error(
                f"고른 재료의 기본량 합이 {x0.sum():.1f}% 로 100 을 넘습니다. "
                f"재료를 줄이거나 범위를 낮춰 주세요.")
            if st.button("← 재료 다시 고르기"):
                _goto(2); st.rerun()
            return
        x0[built.palette.index(built.filler)] = rest

        tgt = {t: iv.goals.get(t, 0.0) for t in built.y_terms}
        lo = np.array([bounds.get(g, (0.0, 100.0))[0] for g in free])
        hi = np.array([bounds.get(g, (0.0, 100.0))[1] for g in free])
        try:
            x = propose_fn(built, tgt, x0, lo, hi,
                           [t for t in iv.free_axes if t in built.y_terms])
        except Exception as e:                                    # noqa: BLE001
            st.error(f"제안에 실패했습니다: {e}")
            return

        st.markdown("##### 배합")
        rows = []
        for g, v in zip(built.palette, x):
            if v <= 1e-4 and g != built.filler:
                continue
            rows.append({"재료": g.replace("ING.", ""), "%": round(float(v), 3)})
        rows.sort(key=lambda r: -r["%"])
        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.caption(f"합계 {x.sum():.2f}%")

        y = built.model.predict(x[None, :])[0]
        st.markdown("##### 기준 대비 예상")
        st.caption("0 = 기준과 같음. 목표와 예상이 다르면 그 축은 고른 재료로 "
                   "거기까지 못 간다는 뜻입니다.")
        st.dataframe(
            {"축": [t.split(".")[-1] for t in built.y_terms],
             "목표": [tgt[t] if t not in iv.free_axes else "상관없음"
                     for t in built.y_terms],
             "예상": [round(float(v), 2) for v in y]},
            use_container_width=True, hide_index=True)

        if np.abs(y).max() > 3.0:
            st.error(
                f"예상이 ±3 척도를 벗어났습니다(최대 {np.abs(y).max():.1f}). "
                f"재료 범위가 너무 넓을 수 있습니다 — 전문가 화면에서 확인하세요.",
                icon="🚨")

        with st.expander("이 배합이 나온 근거"):
            st.write(built.report())
            st.caption(
                "실측 데이터가 없으면 온톨로지의 사전값만으로 낸 제안입니다. "
                "만들어 평가한 결과를 전문가 화면 ⑤ 실험 입력에 넣으면 "
                "다음 제안부터 그 데이터가 반영됩니다.")

        c1, c2 = st.columns(2)
        if c1.button("← 재료 다시 고르기"):
            _goto(2); st.rerun()
        if c2.button("목표 다시 정하기"):
            _goto(1); st.rerun()


def _variants(onto, profile):
    try:
        import palette as pal
        import openpyxl
        wb = openpyxl.load_workbook(pal.DEFAULT_PATH, data_only=True)
        ws = wb["palette"]
        hdr = [str(c.value).strip() if c.value else "" for c in ws[1]]
        iP, iV = hdr.index("프로파일"), hdr.index("목적")
        out = []
        for r in ws.iter_rows(min_row=2, values_only=True):
            if str(r[iP] or "").strip() != profile:
                continue
            v = str(r[iV] or "").strip()
            if v and v not in out:
                out.append(v)
        return out
    except Exception:                                              # noqa: BLE001
        return []
