# -*- coding: utf-8 -*-
"""
통상 사용량을 API 로 채운다 — 이 프로젝트의 첫 API 호출 (2026-09-11).

왜
--
효과 크기(weak/medium/strong)에는 양이 없다. 양은 팔레트의 하한·상한이 정하고
(1 SD = (상한-하한)/2), 그래서 범위가 곧 사전의 단위다. 그 범위를 사람이 재료
118 × 제형 8 을 하나하나 정하는 것은 옳지 않다(사용자). "잔탄을 드레싱에 보통
얼마나 넣나" 는 API 가 잘 아는 종류의 지식이다. docs/bounds_strategy.md 4-5절.

무엇을 묻나 (제형 하나에 한 번, 그 제형에서 어느 축이든 닿는 재료를 전부 묶어서)
    typical_pct        이 제형에서 이 재료를 보통 얼마나 (완제품 중량 %)
    upper_pct          이 이상이면 오프노트·결함이 나타나기 시작하는 지점
    lower_hint_pct     보통 이 아래로는 안 넣는다 — **참고만.** 작업 범위 하한은
                       규칙으로 0 이다 (하한 0 예외는 사람이 정한다)
    dose_response      linear | threshold | saturating — 형태 라벨. 모형은 당분간
                       선형이고, 나중에 E 가 곡률 사전으로 쓴다
    rationale          한 줄 근거
    confidence         high | medium | low

무엇을 하나
    --check   호출하지 않는다. 어느 제형에 어느 재료를 물을지, 토큰 추정만
    --write   호출하고 팔레트에 쓴다. 전부 통상출처=api_draft. 행이 없는 제형은
              행을 만든다(등급 옵션 · 확인 "API 초안 — 검토 필요").
              세 신호와 교차해 어긋난 행을 data/typical_review.xlsx 로 낸다:
                실측 폭 (있으면)         통상이 실측 min~max 안에 있나
                온톨로지 limitations    upper 가 적힌 상한을 넘나
                기능군 typical_use_pct   자릿수가 10배 이상 다르나
    --profile NAME   한 제형만
    --model ID       기본 claude-opus-5

키
--
환경변수 ANTHROPIC_API_KEY 에서만 읽는다 (anthropic.Anthropic() 기본 동작).
코드·파일에 키를 두지 않는다.
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import os
import re
import shutil
import sys

import openpyxl
import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, "engine"), os.path.join(ROOT, "app"), ROOT]

from formulator.v2adapter import V2Ontology            # noqa: E402

PALETTE = os.path.join(ROOT, "data", "palette.xlsx")
REVIEW = os.path.join(ROOT, "data", "typical_review.xlsx")
MODEL = "claude-opus-5"

SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "typical_pct": {"type": "number"},
                    "upper_pct": {"type": "number"},
                    "lower_hint_pct": {"type": "number"},
                    "dose_response": {"type": "string",
                                      "enum": ["linear", "threshold", "saturating"]},
                    "rationale": {"type": "string"},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                },
                "required": ["id", "typical_pct", "upper_pct", "lower_hint_pct",
                             "dose_response", "rationale", "confidence"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["items"],
    "additionalProperties": False,
}

SYSTEM = """You are a food formulation scientist. For each ingredient in a given
food structure/application, give typical usage in the FINISHED PRODUCT (weight %).

Definitions:
- typical_pct: the level a competent formulator would start from for this
  application. Not a legal limit, not an extreme.
- upper_pct: the level above which sensory or physical defects begin
  (off-notes, sliminess, waxiness, grittiness, over-sweetness, gel failure...).
  This is a SENSORY acceptability ceiling, not a regulatory limit.
- lower_hint_pct: below this the ingredient has no practical effect. Reference only.
- dose_response: how the ingredient's main effect scales with dose within
  [0, upper_pct]: "linear" (roughly proportional), "threshold" (little effect
  then a sharp rise, e.g. xanthan viscosity), "saturating" (rises then plateaus).
- rationale: one short sentence, in English.
- confidence: high if this is standard practice; low if the ingredient is
  unusual for this application or highly product-dependent.

Rules: answer for EVERY id given, in the same ids. Numbers are weight % of the
finished product (0-100). If an ingredient is genuinely out of place in this
application, still give the most plausible numbers and set confidence to low.
Return only the JSON object required by the schema."""


def ask_list(onto, profile):
    """그 제형에서 어느 축이든 닿는 재료. 도달 못 하면 통상량을 물을 이유가 없다."""
    eff = onto.effects_for(profile)
    return sorted(g for g, e in eff.items() if e and g != onto.filler_of(profile))


def profile_blurb(onto, profile):
    sp = None
    for cand in onto._s_candidates(profile):
        sp = cand
        break
    if not sp:
        return profile
    ko = (sp.get("ko") or {})
    return f"{sp.get('label')} — {sp.get('definition') or ko.get('definition') or ''}"


def build_prompt(onto, profile, ings):
    lines = [f"Structure / application: {profile_blurb(onto, profile)}", "",
             "Ingredients (id — name — function tags):"]
    for g in ings:
        d = onto.ingredients[g]
        tags = ", ".join(t.replace("FT.", "") for t in (d.get("function_tags") or []))
        lines.append(f"  {g} — {d.get('label') or d.get('ko') or g} — {tags}")
    return "\n".join(lines)


def call_api(client, model, prompt):
    with client.messages.stream(
        model=model,
        max_tokens=32000,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
    ) as stream:
        msg = stream.get_final_message()
    if msg.stop_reason == "refusal":
        raise RuntimeError(f"refused: {msg.stop_details}")
    text = next(b.text for b in msg.content if b.type == "text")
    return json.loads(text)["items"], msg.usage


# ------------------------------------------------------------------ 교차 검사
def measured_range(onto, profile):
    """
    이 제형 위에 선 제품(projects/)의 실측에서 재료별 min~max. 없으면 {}.
    API 는 제형에 묻지만 실측은 제품에 붙어 있다 - 쌀음료 18건은 beverage 의
    검증 데이터다 (사용자: 실측은 기준이 아니라 검증 데이터로).
    """
    out = {}
    for pid, pj in getattr(onto, "projects", {}).items():
        if pj.get("structure") != profile:
            continue
        f = (pj["card"].get("meta") or {}).get("data")
        if not f:
            continue
        try:
            import dataio
            d = dataio.load_warmloop(os.path.join(ROOT, f), onto, pid)
            for i, g in enumerate(d.names):
                lo, hi = float(d.X[:, i].min()), float(d.X[:, i].max())
                if g in out:
                    lo, hi = min(lo, out[g][0]), max(hi, out[g][1])
                out[g] = (lo, hi)
        except Exception:                                  # noqa: BLE001
            pass
    return out


def limitation_upper(onto, g):
    """limitations 의 '> ~0.5%' 같은 상한 문구에서 숫자를 긁는다."""
    out = []
    for lim in (onto.ingredients[g].get("limitations") or []):
        st = str(lim.get("statement") or "")
        m = re.search(r">\s*~?\s*([\d.]+)\s*%", st)
        if m:
            out.append(float(m.group(1)))
    return min(out) if out else None


def tag_typical(onto, g):
    ft = (onto.ingredients[g].get("function_tags") or [None])[0]
    typ = (onto.tags.get(ft) or {}).get("typical_use_pct")
    m = re.findall(r"[\d.]+", str(typ or ""))
    if not m:
        return None
    return float(m[0]) if len(m) == 1 else (float(m[0]) + float(m[1])) / 2


def cross_check(onto, profile, item, meas):
    flags = []
    g, typ, hi = item["id"], item["typical_pct"], item["upper_pct"]
    if hi <= typ:
        flags.append(f"upper({hi}) <= typical({typ})")
    k = hi / typ if typ else float("inf")
    if not (1.5 <= k <= 5):
        flags.append(f"upper/typical = {k:.1f} (기대 1.5~5)")
    if g in meas:
        lo_m, hi_m = meas[g]
        if hi_m > 0 and not (lo_m <= typ <= hi_m * 1.5):
            flags.append(f"실측 {lo_m:.2f}~{hi_m:.2f} 밖")
    lim = limitation_upper(onto, g)
    if lim is not None and hi > lim * 1.5:
        flags.append(f"limitations 상한 {lim}% 보다 큼")
    tt = tag_typical(onto, g)
    if tt and typ > 0 and (typ / tt > 10 or tt / typ > 10):
        flags.append(f"기능군 통상 {tt} 와 자릿수 다름")
    return flags


# ------------------------------------------------------------------ 팔레트 쓰기
def write_palette(onto, profile, items):
    shutil.copy2(PALETTE, PALETTE.replace(".xlsx",
                 f"_백업_{datetime.datetime.now():%y%m%d_%H%M%S}.xlsx"))
    wb = openpyxl.load_workbook(PALETTE)
    ws = wb["palette"]
    hdr = [str(c.value or "").strip() for c in ws[1]]
    col = {h: i + 1 for i, h in enumerate(hdr)}
    existing = {}
    for r in range(2, ws.max_row + 1):
        if str(ws.cell(r, col["프로파일"]).value or "").strip() == profile and \
           not str(ws.cell(r, col.get("목적", 2)).value or "").strip():
            existing[str(ws.cell(r, col["온톨로지ID"]).value).strip()] = r
    n_upd = n_new = 0
    for it in items:
        g = it["id"]
        note = (f"api_draft {datetime.date.today()} · upper {it['upper_pct']}% "
                f"(오프노트 시작) · lower_hint {it['lower_hint_pct']}% · "
                f"{it['dose_response']} · {it['confidence']} · {it['rationale']}")
        if g in existing:
            r = existing[g]
            ws.cell(r, col["통상"]).value = it["typical_pct"]
            ws.cell(r, col["통상출처"]).value = "api_draft"
            ws.cell(r, col["통상근거"]).value = note
            n_upd += 1
        else:
            d = onto.ingredients[g]
            slot, slot_ko = onto.slot_of(g, profile)
            row = {h: "" for h in hdr}
            row.update({"프로파일": profile, "목적": "", "슬롯": slot_ko or slot,
                        "재료": d.get("ko") or d.get("label") or g,
                        "온톨로지ID": g, "등급": "옵션",
                        "하한": 0, "상한": "",           # 상한은 5단계에서 통상×k 로
                        "통상": it["typical_pct"], "통상출처": "api_draft",
                        "통상근거": note, "범위근거": "",
                        "담당축": "", "메모": "", "확인": "API 초안 — 검토 필요"})
            ws.append([row.get(h, "") for h in hdr])
            n_new += 1
    wb.save(PALETTE)
    return n_upd, n_new


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--profile")
    ap.add_argument("--model", default=MODEL)
    a = ap.parse_args()

    onto = V2Ontology()
    # 제품(projects/)은 뺀다 - 통상량은 재료 × 제형이고, 제품은 제형 것을 물려받는다.
    # 제품 고유 통상량이 필요하면 product_card 의 axes 처럼 나중에 덮는다.
    profiles = [a.profile] if a.profile else sorted(
        p for p in onto.profiles if p not in getattr(onto, "projects", {}))
    print("=" * 70)
    print("  통상 사용량 — API 초안" + ("" if a.write else "   (--check: 호출하지 않는다)"))
    print("=" * 70)

    plan = []
    for p in profiles:
        ings = ask_list(onto, p)
        prompt = build_prompt(onto, p, ings)
        plan.append((p, ings, prompt))
        print(f"  {p:<22} 재료 {len(ings):>3}종 · 프롬프트 ~{len(prompt)//4:>5} 토큰")
    if not a.write:
        est_in = sum(len(pr) // 4 + 600 for _, _, pr in plan)
        est_out = sum(len(i) * 60 for _, i, _ in plan)
        print(f"\n  추정: 입력 ~{est_in:,} · 출력 ~{est_out:,} 토큰 · "
              f"{a.model} 기준 약 ${est_in*5/1e6 + est_out*25/1e6:.2f}")
        print("  실제로 호출하려면: python tools/fill_typical_api.py --write   (ANTHROPIC_API_KEY 필요)")
        return 0

    import anthropic
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n  ANTHROPIC_API_KEY 가 없습니다. 환경변수로 넣고 다시 돌리세요. (키는 코드에 안 둡니다)")
        return 2
    client = anthropic.Anthropic()

    review = []
    for p, ings, prompt in plan:
        try:
            items, usage = call_api(client, a.model, prompt)
        except anthropic.RateLimitError as e:
            print(f"  {p}: 속도 제한. retry-after {e.response.headers.get('retry-after')}s"); continue
        except anthropic.APIStatusError as e:
            print(f"  {p}: API 오류 {e.status_code}: {e.message[:80]}"); continue
        got = {it["id"] for it in items}
        missing = [g for g in ings if g not in got]
        meas = measured_range(onto, p)
        n_flag = 0
        for it in items:
            fl = cross_check(onto, p, it, meas)
            if fl:
                n_flag += 1
            review.append((p, onto.ing_label(it["id"]), it["id"], it["typical_pct"],
                           it["upper_pct"], it["lower_hint_pct"], it["dose_response"],
                           it["confidence"], "; ".join(fl), it["rationale"]))
        n_upd, n_new = write_palette(onto, p, items)
        print(f"  {p:<22} 답 {len(items):>3} (누락 {len(missing)}) · 팔레트 갱신 {n_upd} 신규 {n_new} · "
              f"교차검사 걸림 {n_flag} · 토큰 {usage.input_tokens}+{usage.output_tokens}")

    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "typical_review"
    ws.append(["제형", "재료", "ID", "통상%", "상한%(오프노트)", "하한힌트%", "형태",
               "확신", "교차검사 걸림", "근거", "판정", "메모"])
    for c in ws[1]:
        c.font = openpyxl.styles.Font(bold=True)
    review.sort(key=lambda r: (r[8] == "", r[0], r[1]))    # 걸린 것부터
    for r in review:
        ws.append(list(r) + ["", ""])
    for row in ws.iter_rows(min_row=2):
        if row[8].value:
            for c in row:
                c.fill = openpyxl.styles.PatternFill("solid", fgColor="F6EDD8")
    for col, w in zip("ABCDEFGHIJKL", (14, 22, 30, 8, 12, 10, 10, 7, 40, 50, 8, 24)):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A2"
    wb.save(REVIEW)
    print(f"\n  검토표: {REVIEW}  ({len(review)}행, 걸린 것 맨 위)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
