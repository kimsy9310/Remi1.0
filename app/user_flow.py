# -*- coding: utf-8 -*-
"""
사용자 화면 — 단계형 인터뷰.

    ① 무엇을 만드시나요      제형/제품 · **이 제품을 정하는 것**(정체성 축 칩) · 기준 제품
    ② 어떻게 바꾸고 싶나요    정체성 축은 세기만 · 바꿀 축을 칩으로 고르고 그것만 슬라이더
    ③ 무엇을 쓰시나요        슬롯별 재료 고르기
    ④ 배합 제안             엔진이 낸 배합과 그 근거

② 가 무엇을 묻는지는 B1 `SCOPE` 가 정한다(interview.scope). 카드의 tier 와
default_goal 만 읽으면 정해지는 일이라 새로 만들 질문이 없다.

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


def _ask(q, iv, strength=False):
    """
    축 하나에 슬라이더 하나. 되돌려 주는 것은 (목표값, '상관없음' 여부).

    strength=True 면 정체성 축이다. 눈금은 같고 부르는 말만 '얼마나 강하게'로
    바뀐다 — 만들 것을 이미 정한 사람에게 '이 축을 바꿀까요'는 질문이 아니다.
    """
    key = "strength" if strength else "label"
    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        c1.markdown(f"**{q['label']}**")
        free = c2.checkbox("상관없음", key=f"uf_free_{q['term']}",
                           value=q["term"] in iv.free_axes)
        hint = q["hint"]
        if q.get("target"):
            hint = (hint + " · " if hint else "") + f"목표: {q['target']}"
        if hint:
            st.caption(hint)
        vals = [o["value"] for o in q["options"]]
        cur = iv.goals.get(q["term"], 0.0)
        sel = st.select_slider(
            " ", options=vals, value=cur if cur in vals else 0.0,
            format_func=lambda v, q=q: next(
                o[key] for o in q["options"] if o["value"] == v),
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
    return (0.0 if free else float(sel)), bool(free)


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
        choices = iq.product_choices(onto)
        labels = [c["label"] + ("  (제품)" if c["is_product"] else "")
                  for c in choices]
        idx = 0
        if iv.profile:
            for i, c in enumerate(choices):
                if c["profile"] == iv.profile:
                    idx = i
        pick = st.radio("제품 종류", range(len(choices)),
                        format_func=lambda i: labels[i], index=idx)
        ch = choices[pick]
        # 정의만 보여 준다. boundary_note 는 "SC.solution 과의 경계는..." 처럼
        # 이 제형이 아닌 것을 가려내는 글이라 온톨로지를 다루는 사람에게는
        # 필요하지만 만들 사람에게는 첫 화면부터 벽이 된다.
        if ch["definition"]:
            st.caption(ch["definition"])

        vars_ = _variants(onto, ch["profile"])
        variant = None
        if vars_:
            v = st.selectbox("목적", ["(기본)"] + vars_,
                             help="같은 제형이라도 목적에 따라 재료 범위가 달라집니다.")
            variant = None if v == "(기본)" else v

        # ---- 이 제품을 정하는 것 (A4 의 정체성 축 칩)
        #
        # 이 축들이 ② 에서 여기로 올라왔다. 매운맛·건고추 향은 "기준보다 더 매울까"
        # 를 물을 대상이 아니라 무엇을 만드는지 자체다. 카드에 기본값이 박혀 있고
        # ("default for fermented hot sauce ... Swappable") 지금까지 UI 가 그걸
        # 읽지 않아 현탁액을 고른 사람 모두에게 발효 핫소스의 축이 나갔다.
        st.markdown("##### 이 제품을 정하는 것")
        st.caption(
            "이 제품을 이 제품답게 만드는 향·맛입니다. 만들려는 것과 다르면 "
            "지우고 다른 것을 더하세요. 지운 축은 신경 쓰지 않습니다. "
            "얼마나 강하게 할지는 다음 단계에서 묻습니다.")
        cands = iq.identity_candidates(onto, ch["profile"])
        clab = {c["term"]: c["label"] + ("" if c["modeled"] else "  (기록만)")
                for c in cands}
        base = (iv.identity_axes
                if iv.identity_axes is not None and iv.profile == ch["profile"]
                else iq.default_identity(onto, ch["profile"]))
        # 키에 제형을 넣어 둔다 — 제형을 바꾸면 축이 통째로 갈리므로 앞 제형의
        # 선택이 위젯에 남아 있으면 안 된다.
        ident = st.multiselect(
            " ", [c["term"] for c in cands],
            default=[t for t in base if t in clab],
            format_func=lambda t: clab[t],
            key=f"uf_ident_{ch['profile']}", label_visibility="collapsed",
            placeholder="정하는 향·맛을 고르세요")
        if any(not c["modeled"] for c in cands if c["term"] in ident):
            st.caption("'(기록만)' 은 이 제형의 카드에 아직 없는 축입니다. "
                       "골라 두면 남지만 배합 계산에는 들어가지 않습니다.")

        st.markdown("##### 기준으로 삼을 제품")
        st.caption(
            "이 도구는 **기준 대비 얼마나 다른가**로 맛을 다룹니다. 잘 아는 제품을 "
            "하나 정해 두면 다음 질문이 '그것보다 더/덜'이 되어 답하기 쉬워집니다.")
        bm = st.text_input("예: 시중 ○○ 제품, 지난 시제품 3번",
                           value=iv.benchmark, placeholder="이름만 적어두셔도 됩니다")

        if st.button("다음", type="primary"):
            if iv.profile != ch["profile"]:
                iv.reset_answers()                   # 제품이 바뀌면 초기화
            iv.profile, iv.variant, iv.benchmark = ch["profile"], variant, bm
            iv.identity_axes = list(ident)
            _goto(1)
            st.rerun()

    # ================================================== ② 어떻게 바꾸나
    elif step == 1:
        st.subheader("기준과 비교해 어떻게 바꾸고 싶으세요?")
        if iv.benchmark:
            st.caption(f"기준: **{iv.benchmark}**")

        # B1 SCOPE 가 물어볼 축을 나눈다. 화면은 그 셋을 그대로 따른다.
        sc = iq.scope(onto, iv.profile)
        by_term = {q["term"]: q
                   for q in sc["identity"] + sc["adjust"] + sc["defect"]}
        ident = (iv.identity_axes if iv.identity_axes is not None
                 else iq.default_identity(onto, iv.profile))

        # 답을 매번 새로 짓는다. 칩에서 뺀 축이 지난번 값을 들고 남는 일을 막는다.
        goals, free = {}, []

        # ---- 정체성 축: 세기만 묻는다
        ident_q = [by_term[t] for t in ident if t in by_term]
        if ident_q:
            st.markdown("##### 이 제품을 정하는 것")
            st.caption("① 에서 고른 축입니다. **얼마나 강하게** 만 정하면 됩니다.")
            for q in ident_q:
                v, f = _ask(q, iv, strength=True)
                goals[q["term"]] = v
                if f:
                    free.append(q["term"])
        extra = [t for t in ident if t not in by_term]
        if extra:
            st.caption("이 제형의 카드에 아직 없어 적어만 두는 축: "
                       + ", ".join(iq.axis_label(t, onto) for t in extra))
        # ① 에서 지운 정체성 축은 붙잡지 않는다. 0(기준과 같게)으로 두면 이 제품이
        # 그 축을 그대로 가져간다는 뜻이 되어, 지운 뜻과 정반대가 된다.
        dropped = [q["term"] for q in sc["identity"] if q["term"] not in ident]
        if dropped:
            free += dropped
            st.caption("① 에서 지운 축은 신경 쓰지 않습니다: "
                       + ", ".join(iq.axis_label(t, onto) for t in dropped))

        # ---- 조절 축: 바꿀 것을 먼저 고르고, 고른 것만 묻는다
        adj = [q for q in sc["adjust"] if q["term"] not in ident]
        if adj:
            st.markdown("##### 바꾸고 싶은 것")
            st.caption("고르지 않은 축은 기준과 같게 둡니다. "
                       "바꿀 것만 고르세요 — 열 개를 한꺼번에 붙잡으면 "
                       "정작 바꾸려는 축이 눌립니다.")
            lab = {q["term"]: q["label"] for q in adj}
            picked = st.multiselect(
                " ", [q["term"] for q in adj],
                default=[t for t in iv.changed if t in lab],
                format_func=lambda t: lab[t], key="uf_changed",
                label_visibility="collapsed", placeholder="바꿀 것을 고르세요")
            iv.changed = list(picked)
            for q in adj:
                if q["term"] in picked:
                    v, f = _ask(q, iv)
                    goals[q["term"]] = v
                    if f:
                        free.append(q["term"])
                else:
                    goals[q["term"]] = 0.0

        # ---- 결함 축: 먼저 묻지 않고 접어 둔다
        dfc = [q for q in sc["defect"] if q["term"] not in ident]
        if dfc:
            lab = {q["term"]: q["label"] for q in dfc}
            with st.expander("신경 쓰이는 것이 있나요"):
                st.caption("낮을수록 좋은 축입니다. 기준 제품에서 거슬렸던 것이 "
                           "있으면 고르세요. 고르지 않으면 기준만큼으로 둡니다.")
                picked = st.multiselect(
                    " ", [q["term"] for q in dfc],
                    default=[t for t in iv.concerns if t in lab],
                    format_func=lambda t: lab[t], key="uf_concerns",
                    label_visibility="collapsed", placeholder="거슬리는 것을 고르세요")
                iv.concerns = list(picked)
                for q in dfc:
                    if q["term"] in picked:
                        v, f = _ask(q, iv)
                        goals[q["term"]] = v
                        if f:
                            free.append(q["term"])
                    else:
                        goals[q["term"]] = 0.0

        iv.goals, iv.free_axes = goals, free

        c1, c2 = st.columns(2)
        if c1.button("← 이전"):
            _goto(0); st.rerun()
        if c2.button("다음", type="primary"):
            _goto(2); st.rerun()

    # ================================================== ③ 재료
    elif step == 2:
        st.subheader("무엇을 쓰시나요?")
        ptab = load_palette(iv.profile, iv.variant)
        if ptab is None or not [r for r in ptab.rows if r["등급"] != "제외"]:
            st.info("재료 후보를 세우는 중입니다. 잠시 후 다시 시도해 주세요.")
            if st.button("← 이전"):
                _goto(1); st.rerun()
            return
        st.caption("가지고 계신 재료만 고르세요. 고르지 않은 재료는 배합에 쓰이지 않습니다. "
                   "각 재료 옆의 화살표는 그 재료가 무엇을 움직이는지입니다. "
                   "그대로 두셔도 됩니다 — 미리 골라 둔 조합으로 제안이 나갑니다.")

        groups = iq.ingredient_questions(ptab, onto, iv.profile)
        for g in groups:
            head = f"**{g['slot']}**" + ("  · 필수" if g["required"] else "")
            with st.expander(head, expanded=g["required"] or bool(iv.chosen.get(g["slot"]))):
                if g.get("unslotted"):
                    st.caption("이전 실험에 쓰인 재료입니다. 전부 켜 둔 상태가 기본입니다.")
                opts = [i["id"] for i in g["items"]]
                lab = {i["id"]: i for i in g["items"]}
                default = iv.chosen.get(g["slot"], g["default"])
                sel = st.multiselect(
                    " ", opts,
                    default=[x for x in default if x in opts],
                    format_func=lambda x: (
                        lab[x]["label"]
                        + (f"  {' '.join(lab[x]['moves'])}" if lab[x]["moves"] else "")),
                    key=f"uf_ing_{g['slot']}", label_visibility="collapsed")
                iv.chosen[g["slot"]] = sel
                for x in sel:
                    it = lab[x]
                    bits = []
                    if it["bounds"][1] is not None:
                        bits.append(f"보통 {it['bounds'][1]:g}% 까지 씁니다")
                    if it["grade"] == "제한":
                        bits.append("적게 쓰는 것이 좋은 재료입니다")
                    if not it["moves"]:
                        bits.append("맛을 바꾸기보다 제품의 꼴을 잡는 재료입니다")
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
            st.warning(
                "고른 재료를 모두 넣으면 100% 를 넘습니다. ③ 으로 돌아가 재료를 "
                "몇 가지 빼 주세요.", icon="⚠️")
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

        name = {r["온톨로지ID"]: iq._name(onto, r["온톨로지ID"], r["재료"])
                for r in (ptab.rows if ptab else [])}
        for g in built.palette:
            name.setdefault(g, iq._name(onto, g, None))

        st.markdown("##### 배합")
        rows = []
        for g, v, v0 in zip(built.palette, x, x0):
            if v <= 1e-4 and v0 <= 1e-4:
                continue
            d = float(v) - float(v0)
            rows.append({"재료": name.get(g, g.replace("ING.", "")),
                         "%": round(float(v), 3),
                         "출발점 대비": ("—" if abs(d) < 5e-4 else f"{d:+.3f}")})
        rows.sort(key=lambda r: -r["%"])
        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.caption(f"합계 {x.sum():.2f}%  ·  '출발점 대비' 는 목표를 맞추려고 "
                   f"이 도구가 움직인 양입니다.")

        y = built.model.predict(x[None, :])[0]
        st.markdown("##### 기준 대비 예상")
        st.caption("0 = 기준과 같음. 목표와 예상이 다르면 그 축은 고른 재료로 "
                   "거기까지 못 간다는 뜻입니다.")
        st.dataframe(
            {"축": [iq.axis_label(t, onto) for t in built.y_terms],
             "목표": [tgt[t] if t not in iv.free_axes else "상관없음"
                     for t in built.y_terms],
             "예상": [round(float(v), 2) for v in y]},
            use_container_width=True, hide_index=True)

        if np.abs(y).max() > 3.0:
            st.warning(
                "목표가 이 재료들로 갈 수 있는 범위를 넘어섭니다. 목표를 조금 "
                "낮추거나 ③ 에서 재료를 더 고르시면 현실적인 배합이 나옵니다.",
                icon="⚠️")

        with st.expander("왜 이렇게 나왔나요"):
            _why(onto, built, iv, tgt, x, x0, name)

        c1, c2 = st.columns(2)
        if c1.button("← 재료 다시 고르기"):
            _goto(2); st.rerun()
        if c2.button("목표 다시 정하기"):
            _goto(1); st.rerun()


def _why(onto, built, iv, tgt, x, x0, name):
    """
    제안의 근거를 사람 말로.

    엔진의 report() 는 Γ₀ 비영 계수와 Λ 확신도를 찍는다 — 모형을 손보는
    사람에게는 맞는 말이지만, 만들 사람이 알고 싶은 것은 "내가 올려 달라고 한
    축을 무엇으로 올렸나" 하나다. 같은 사실을 그 질문에 맞춰 다시 쓴다.
    """
    eff = onto.effects_for(iv.profile)
    moved = sorted(
        ((g, float(v) - float(v0)) for g, v, v0 in zip(built.palette, x, x0)),
        key=lambda gv: -abs(gv[1]))

    said = [t for t in built.y_terms
            if t not in iv.free_axes and abs(tgt.get(t, 0.0)) > 1e-9]
    if said:
        st.markdown("**바꿔 달라고 하신 것**")
        for t in said:
            lv = [(g, d) for g, d in moved
                  if abs(d) > 5e-4 and t in (eff.get(g) or {})]
            if not lv:
                st.write(f"- {onto.label(t)}: 움직일 재료가 없어 그대로입니다.")
                continue
            bits = ", ".join(
                f"{name.get(g, g.replace('ING.', ''))} {d:+.2f}%"
                for g, d in lv[:3])
            st.write(f"- {onto.label(t)}: {bits}")
    else:
        st.write("바꿔 달라고 하신 축이 없어, 기준과 같게 맞춘 배합입니다.")

    st.markdown("**이 숫자를 얼마나 믿을 수 있나요**")
    st.write("- 재료가 무엇을 하는지에 대한 일반 지식으로 계산했습니다. "
             "방향은 믿을 만하지만 크기는 어긋날 수 있습니다.")
    st.write("- 이 배합을 한 번 만들어 맛을 평가해 넣으시면, 다음 제안부터 "
             "그 결과가 반영되어 훨씬 정확해집니다.")
    thin = [onto.label(t) for t in said
            if len([g for g in built.palette if t in (eff.get(g) or {})]) < 2]
    if thin:
        st.write(f"- {', '.join(thin)} 은(는) 손댈 재료가 하나뿐이라 "
                 f"조절 폭이 좁습니다.")


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
