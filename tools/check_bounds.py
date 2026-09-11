# -*- coding: utf-8 -*-
"""
팔레트 범위 검사 · 초안 생성 (docs/bounds_strategy.md 4·5절, 2026-09-11).

두 가지를 한다.

--check (기본)   지금 팔레트의 행마다 규칙에 걸리는지 낸다. 파일을 안 건드린다.
    R1  하한 ≠ 0           하한 0 규칙. 예외(필수·정체성 재료)는 사람이 정한다
    R2  통상 없음          통상 열이 비어 있다 -> fill_typical_api 가 먼저
    R3  통상 ∉ [하한,상한]  통상이 범위 밖
    R4  k = 상한/통상       1.5~5 밖. 상한이 통상의 몇 배인가가 범위의 전부다
                          (하한 0 이면 1 SD = 상한/2 = 통상 × k/2)
    R5  범위근거 없음       하한·상한이 있는데 근거가 비었다

--write          범위가 없는 행에 초안을 쓴다:  하한 0 · 상한 = 통상 × k.
    k 는 API 가 준 upper(통상근거에 'upper N%' 로 적혀 있다)에서 오고, 없으면
    기능군별 기본 배수(K_BY_TAG)를 쓴다. 전부 범위근거 'draft ...' 로 표시.
    이미 범위가 있는 행은 건드리지 않는다.

    python tools/check_bounds.py
    python tools/check_bounds.py --write
"""
from __future__ import annotations

import datetime
import io
import os
import re
import shutil
import sys

import openpyxl

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, "engine")]
from formulator.v2adapter import V2Ontology, RANGE_TO_SD    # noqa: E402

PALETTE = os.path.join(ROOT, "data", "palette.xlsx")

# 기능군별 기본 배수 (상한 = 통상 × k). API upper 가 없을 때만. 초안이다.
#   감미료·유지처럼 감각 최적점 근처에서 쓰이는 것은 좁고, 향료·산미료처럼
#   비율로 넓게 견디는 것은 넓다. 사용자: "재료(또는 기능군)마다 다름".
K_BY_TAG = {
    "FT.sweetener": 1.7, "FT.fat_source": 2.0, "FT.bulking_agent": 2.0,
    "FT.fat_replacer": 2.0, "FT.milk_protein": 2.0, "FT.protein": 2.0,
    "FT.thickener": 2.5, "FT.stabilizer": 2.5, "FT.emulsifier": 2.5,
    "FT.fpd_agent": 2.0, "FT.aw_depressant": 2.0, "FT.particulate": 2.5,
    "FT.acidulant": 3.0, "FT.umami_source": 3.0, "FT.fermented_paste": 2.5,
    "FT.flavorant": 5.0, "FT.aroma_oil": 5.0, "FT.aromatic_allium": 4.0,
    "FT.pungent_principle": 3.0, "FT.colorant": 5.0, "FT.preservative": 2.0,
    "FT.mineral_fortifier": 3.0, "FT.firming_agent": 3.0, "FT.weighting_agent": 2.0,
}
K_DEFAULT = 3.0
K_OK = (1.5, 5.0)


def read_rows():
    wb = openpyxl.load_workbook(PALETTE, data_only=True)
    ws = wb["palette"]
    hdr = [str(c.value or "").strip() for c in ws[1]]
    rows = []
    for i, r in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        d = dict(zip(hdr, r))
        if d.get("온톨로지ID"):
            d["_row"] = i
            rows.append(d)
    return hdr, rows


def fnum(v):
    try:
        return None if v in (None, "") else float(v)
    except (TypeError, ValueError):
        return None


def api_upper(note):
    m = re.search(r"upper\s*([\d.]+)\s*%", str(note or ""))
    return float(m.group(1)) if m else None


def check(onto, rows):
    hits = []
    for d in rows:
        lo, hi, typ = fnum(d.get("하한")), fnum(d.get("상한")), fnum(d.get("통상"))
        g = d["온톨로지ID"]
        f = []
        if lo is not None and lo != 0:
            f.append("R1 하한≠0")
        if typ is None:
            f.append("R2 통상 없음")
        else:
            if lo is not None and hi is not None and not (lo <= typ <= hi):
                f.append(f"R3 통상 {typ} ∉ [{lo},{hi}]")
            if hi is not None and typ > 0:
                k = hi / typ
                if not (K_OK[0] <= k <= K_OK[1]):
                    f.append(f"R4 k={k:.1f}")
        if lo is not None and hi is not None and not str(d.get("범위근거") or "").strip():
            f.append("R5 근거 없음")
        if f:
            hits.append((d["프로파일"], onto.ing_label(g) if g in onto.ingredients else g,
                         lo, hi, typ, "; ".join(f)))
    return hits


def write_drafts(onto, hdr, rows, reset_old=False):
    """
    reset_old=False  범위가 없는 행에만 쓴다 (기본)
    reset_old=True   옛 범위(실측 폭·손표)도 걷어내고 통상 기준으로 다시 쓴다.
                     사용자: "기존의 중앙값은 잊고 처음부터". 옛 값은 범위근거에
                     '이전 lo~hi' 로 남긴다. API 통상량을 검사한 뒤에 쓸 것.
    """
    shutil.copy2(PALETTE, PALETTE.replace(".xlsx",
                 f"_백업_{datetime.datetime.now():%y%m%d_%H%M%S}.xlsx"))
    wb = openpyxl.load_workbook(PALETTE)
    ws = wb["palette"]
    col = {h: i + 1 for i, h in enumerate(hdr)}
    n = 0
    for d in rows:
        lo, hi, typ = fnum(d.get("하한")), fnum(d.get("상한")), fnum(d.get("통상"))
        if typ is None or typ <= 0:
            continue
        had = lo is not None and hi is not None
        if had and not reset_old:
            continue                                   # 있는 범위는 안 건드린다
        prev = f" · 이전 {lo}~{hi}" if had else ""
        up = api_upper(d.get("통상근거"))
        if up and up > typ:
            hi_new, why = up, "API upper(오프노트 시작)"
        else:
            g = d["온톨로지ID"]
            ft = (onto.ingredients.get(g, {}).get("function_tags") or [None])[0]
            k = K_BY_TAG.get(ft, K_DEFAULT)
            hi_new, why = round(typ * k, 4), f"통상 × {k} ({(ft or '기능군 없음').replace('FT.', '')})"
        r = d["_row"]
        ws.cell(r, col["하한"]).value = 0
        ws.cell(r, col["상한"]).value = hi_new
        ws.cell(r, col["범위근거"]).value = (
            f"draft {datetime.date.today()} · 하한 0 (규칙) · 상한 {hi_new} = {why} · "
            f"1 SD = {hi_new / RANGE_TO_SD:.3g}%p{prev}")
        n += 1
    wb.save(PALETTE)
    return n


def main(write=False, reset_old=False):
    onto = V2Ontology()
    hdr, rows = read_rows()
    hits = check(onto, rows)
    print("=" * 70)
    print(f"  팔레트 범위 검사 — {len(rows)}행 · 걸린 행 {len(hits)}" + ("" if write else "   (--check)"))
    print("=" * 70)
    from collections import Counter
    c = Counter()
    for h in hits:
        for f in h[5].split("; "):
            c[f.split(" ")[0]] += 1
    print("  규칙별:", dict(c))
    for prof, g, lo, hi, typ, f in hits[:25]:
        print(f"   {prof:<13} {g[:20]:<22} 하한 {lo!s:>7} 상한 {hi!s:>8} 통상 {typ!s:>7}  {f}")
    if len(hits) > 25:
        print(f"   … 그 밖 {len(hits) - 25}행")
    if write:
        n = write_drafts(onto, hdr, rows, reset_old=reset_old)
        print(f"\n  초안 범위를 쓴 행: {n}  "
              + ("(옛 범위도 걷어냄)" if reset_old else "(통상이 있고 범위가 없던 행만)"))
    else:
        print("\n  초안을 쓰려면: python tools/check_bounds.py --write"
              "   (옛 범위까지 다시 쓰려면 --write --reset-old)")
    return 0


if __name__ == "__main__":
    sys.exit(main(write="--write" in sys.argv, reset_old="--reset-old" in sys.argv))
