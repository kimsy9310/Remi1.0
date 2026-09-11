# -*- coding: utf-8 -*-
"""
jar_5 와 diff_7 을 합친다 — 전부 차이 척도다 (docs/척도정의_전략.md 4절, 사용자 승인 2026-09-11).

무엇이 문제였나
  카드의 scale_type 이 둘로 갈려 있었다.
      jar_5    JAR(Just-About-Right). "너무 적다 / 딱 좋다 / 너무 많다" 를 묻는
               소비자 100명 기법이다. 우리 루프에 맞지 않는다
      diff_7   기준 대비 차이 7점(-3..+3). 훈련 안 된 소수 패널이 벤치마크와
               나란히 비교한다. 우리 루프가 이것이다
  그런데
    1 같은 축이 어떤 제형에서는 jar_5, 다른 제형에서는 diff_7 이다 (6개 축).
      축의 성격으로 갈린 게 아니라 파일을 쓴 사람이 달랐던 것이다.
    2 코드가 scale_type 을 읽는 곳이 없다. 앱은 63장이든 30장이든 똑같이
      "기준 대비 -3..+3" 으로 묻는다. 낡은 표시다.
    3 jar_target 34건이 사실 default_goal 의 되풀이다 -
      'match benchmark' 21건 = maintain, 'none detectable' 5건 = minimize.

무엇을 하나
  scale_type: jar_5 -> diff_7          필드는 남긴다. 정본 로더가 필수로 검증한다
  method: JAR -> benchmark_difference  같은 이유
  jar_target                           지운다. default_goal 이 이미 그 뜻이다.
                                       단, default_goal 과 어긋나는 것은 남기고 보고한다
  ko.jar_target                        같이 지운다 (화면 문구는 anchors 가 담당)

동작은 안 바뀐다. 메타데이터가 실제와 맞아지는 것뿐이다.

    python tools/merge_jar_diff.py            # 무엇이 바뀌는지만
    python tools/merge_jar_diff.py --write    # 실제로 바꾼다
"""
from __future__ import annotations

import glob
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = sorted(glob.glob(os.path.join(ROOT, "ontology_v2", "layers", "layerM_*.yaml"))) + \
        sorted(glob.glob(os.path.join(ROOT, "projects", "*", "product_card.yaml")))

# jar_target 문구 -> 그것이 함의하는 default_goal. 어긋나면 지우지 않고 보고한다.
JAR_MEANS = {
    "match benchmark": "maintain",
    "none detectable": "minimize",
    "no visible ring": "minimize",
    "no visible phase split": "minimize",
    "coats like benchmark": "maintain",
    "not gummy": "minimize",
    "not greasy": "minimize",
}


def convert(text):
    """텍스트로 고친다 — 앵커·주석을 살린다. (새 텍스트, 통계, 어긋남)"""
    n = dict(scale=0, method=0, jar=0, ko_jar=0)
    keep = []
    lines = text.split("\n")
    out = []
    cur_goal = None
    # default_goal 은 jar_target 보다 뒤에 올 수도 있어 카드 단위로 두 번 훑는다.
    # 카드 경계는 "- term_id:" 다.
    cards, buf = [], []
    for ln in lines:
        if re.match(r"^\s*-\s*term_id:", ln) or re.match(r"^  L\.[a-z]+\.\w+:\s*$", ln):
            if buf:
                cards.append(buf)
            buf = [ln]
        else:
            buf.append(ln)
    if buf:
        cards.append(buf)
    for card in cards:
        goal = None
        for ln in card:
            m = re.match(r"^\s*default_goal:\s*(\S+)", ln)
            if m:
                goal = m.group(1)
        new_card = []
        for ln in card:
            if re.match(r"^\s*scale_type:\s*jar_5\s*$", ln):
                new_card.append(ln.replace("jar_5", "diff_7")); n["scale"] += 1
                continue
            if re.match(r"^\s*method:\s*JAR\s*$", ln):
                new_card.append(ln.replace("JAR", "benchmark_difference")); n["method"] += 1
                continue
            m = re.match(r"^(\s*)jar_target:\s*(.+?)\s*$", ln)
            if m and not ln.strip().startswith("#"):
                indent, val = m.group(1), m.group(2).strip().strip("'\"")
                # ko 블록 안(들여쓰기 4 이상)이면 화면 문구다 - 지운다
                if len(indent) >= 4:
                    n["ko_jar"] += 1
                    continue
                implied = JAR_MEANS.get(val)
                if implied is None or (goal and implied != goal):
                    keep.append((val, goal))
                    new_card.append(ln)          # 어긋나면 남긴다
                else:
                    n["jar"] += 1
                continue
            new_card.append(ln)
        out.extend(new_card)
    return "\n".join(out), n, keep


def main(write=False):
    tot = dict(scale=0, method=0, jar=0, ko_jar=0)
    kept_all = []
    print("=" * 66)
    print("  jar_5 / JAR / jar_target  ->  diff_7 / benchmark_difference / (default_goal)"
          + ("" if write else "   미리보기"))
    print("=" * 66)
    for f in FILES:
        src = io.open(f, encoding="utf-8").read()
        new, n, keep = convert(src)
        if new == src:
            continue
        rel = os.path.relpath(f, ROOT).replace("\\", "/")
        print(f"  {rel:<52} scale {n['scale']:>2} · method {n['method']:>2} · "
              f"jar_target 삭제 {n['jar']:>2} · ko.jar_target {n['ko_jar']:>2}")
        for k in tot:
            tot[k] += n[k]
        for val, goal in keep:
            kept_all.append((rel, val, goal))
        if write:
            io.open(f, "w", encoding="utf-8", newline="\n").write(new)
    print(f"\n  합계  scale_type {tot['scale']} · method {tot['method']} · "
          f"jar_target 삭제 {tot['jar']} · ko.jar_target 삭제 {tot['ko_jar']}")
    if kept_all:
        print(f"\n  default_goal 과 어긋나 **남긴** jar_target {len(kept_all)}건 — 사람이 볼 것:")
        for rel, val, goal in kept_all:
            print(f"     {rel:<44} '{val}'  vs  default_goal={goal}")
    if not write:
        print("\n  실제로 바꾸려면: python tools/merge_jar_diff.py --write")
    return 0


if __name__ == "__main__":
    sys.exit(main(write="--write" in sys.argv))
