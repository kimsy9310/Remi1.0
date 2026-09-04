# -*- coding: utf-8 -*-
"""
공정 기록 — 1 단계 (최소 정보 표준).

왜 필요한가
-----------
엔진은 관능을 배합의 선형 함수로 본다(y = Γᵀz). 이 식에 공정이 없다. 두 시료가
**다른 공정으로** 만들어졌고 하나가 더 크리미하면, 적합은 그 차이를 재료 계수에
얹는다. 경고도 잔차 이상도 뜨지 않고 조용히 틀린다.

Cornell(1982)이 정식화한 crossed mixture-process design 의 언어로는, 배합 계수가
공정 설정의 함수다 — y = Σ βᵢ(z)·xᵢ. 우리 Γ 는 어느 z 에서 잰 β(z) 인지 모르는
값이다.

1 단계는 이것을 **풀지 않고 막는다.** 공정을 모델링하지 않고 **기록**만 해서
다른 공정의 데이터가 한 덩어리로 적합되는 것을 차단한다. 생물학이 재현성
위기에 내놓은 최소 정보 표준(MIAME/MIBBI)과 같은 발상이다.

여기서 값이 아니라 **동일성**만 있으면 된다. "같은 공정이었나" 에 답할 수 있으면
오염은 막힌다. 값은 2 단계(Layer O)에서 필요하고, 그때 확장한다.

무엇을 묻는지는 온톨로지가 정한다
---------------------------------
제형마다 core 축이 어떤 파라미터에 걸려 있는지는 R-1 을 타고 **계산된다.**
공정 질문도 관능 질문처럼 하드코딩하지 않는다 — `fields()` 가 그 계산이다.

    아이스크림  core 5축 중 4축이 공정에 걸린다 (얼음 결정·지방 부분합일·오버런·믹스 점도)
    쌀음료      core 5축 중 1축                (겉보기 점도)

그래서 제형마다 묻는 개수가 다르고, 대개 2~4 개다.

자세한 배경: docs/공정_전략.md
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

SHEET = "process"

# 규모. 같은 조작이라도 닿는 범위가 다르다 — 주방에서 500 bar 는 없다.
SCALES = ["주방", "파일럿", "공장"]

# ---------------------------------------------------------------- 조작
# 1 단계에서는 전부 자유 서술이다. 값을 해석하지 않고 동일성만 본다.
OPS = {
    "hydrate":  dict(ko="믹스 준비",   ask=["수화·용해 방법과 시간"]),
    "heat":     dict(ko="가열",        ask=["가열 온도와 시간 (안 하면 '없음')"]),
    "emulsify": dict(ko="유화·균질",   ask=["장비", "세기 (압력·rpm·시간 중 아는 대로)"]),
    "grind":    dict(ko="분쇄",        ask=["장비", "굵기 (체눈·메시·'고움/굵음')"]),
    "freeze":   dict(ko="동결",        ask=["장비", "동결 시간"]),
    "aerate":   dict(ko="공기 넣기",   ask=["오버런 또는 휘핑 정도"]),
    "store":    dict(ko="보관",        ask=["보관 온도와 기간"]),
}

# 파라미터 -> 그것을 정하는 조작. Layer O 가 생기면 이 표는 거기로 옮겨 간다.
PARAM_OP = {
    "P.droplet_size_d32":       "emulsify",
    "P.turbidity_cloud":        "emulsify",
    "P.particle_size_d50":      "grind",
    "P.particle_size_d90":      "grind",
    "P.ice_crystal_size":       "freeze",
    "P.fat_destabilization":    "freeze",
    "P.ice_recrystallization":  "store",
    "P.overrun":                "aerate",
    "P.mix_viscosity":          "hydrate",
    "P.apparent_viscosity":     "heat",
    "P.yield_stress":           "heat",
    "P.creaming_index":         "store",
    "P.coalescence_rate":       "store",
}


def fields(onto, profile):
    """
    이 제형에서 물어야 할 조작. 온톨로지에서 계산한다.

    core 축 -> (R-1) -> 파라미터 -> 조작. 같은 조작을 여러 파라미터가 가리키면
    한 번만 묻는다(아이스크림의 동결이 얼음 결정과 지방 부분합일 둘을 정한다).

    반환: [{op, ko, ask[], because[]}] — because 는 "왜 묻는지" 라 화면에 쓴다.
    """
    core = {c["term_id"] for c in onto._ref.load_cards(profile, onto.layers)
            if c["tier"] == "core" and c.get("evidence_required") != "sample_aged"}
    scopes = set(onto.profiles[profile]["scopes"])

    hit = {}
    for r in onto.stack["R"]["relations_proxy"]:
        op = PARAM_OP.get(r["parameter"])
        if not op or r["percept"] not in core:
            continue
        if r.get("scope") not in scopes and r.get("scope") != "any":
            continue
        hit.setdefault(op, set()).add(r["percept"])

    out = []
    for op, percepts in hit.items():
        out.append(dict(op=op, ko=OPS[op]["ko"], ask=list(OPS[op]["ask"]),
                        because=sorted(onto.label(t) for t in percepts)))
    out.sort(key=lambda d: (-len(d["because"]), d["ko"]))
    return out


# ---------------------------------------------------------------- 카드
@dataclass
class Card:
    """공정 한 벌. 프로젝트마다 한 장이고 시료마다 지문으로 붙는다."""
    profile: str = ""
    scale: str = ""
    answers: dict = field(default_factory=dict)   # {"emulsify.장비": "핸드블렌더"}
    block: str = ""                               # 사람이 읽는 이름 (RM-P1 등)
    declared_by: str = ""
    declared_at: str = ""
    note: str = ""

    def fingerprint(self):
        """
        같으면 같은 공정이다. 공백과 대소문자는 무시한다 — 사람이 적는 칸이라
        "핸드블렌더" 와 "핸드 블렌더" 가 다른 공정이 되면 안 된다.
        """
        parts = [self.profile.strip(), self.scale.strip()]
        for k in sorted(self.answers):
            v = re.sub(r"\s+", "", str(self.answers[k] or "")).lower()
            parts.append(f"{k}={v}")
        return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:12]

    def is_declared(self):
        """
        선언된 카드인가.

        **블록 이름만 있어도 선언이다.** 1 단계의 목적은 값이 아니라 동일성이라
        (5.1 (b)), "이 데이터는 RM-P1 공정이다" 만으로 다른 공정과 섞이는 것을
        막을 수 있다. 세부를 다 채워야 선언으로 치면, 세부를 모르는 과거
        데이터는 영영 선언할 수 없게 된다 — 그건 정확히 우리가 처한 경우다.
        """
        return bool(self.block.strip() or self.scale.strip() or any(
            str(v or "").strip() for v in self.answers.values()))

    def summary(self):
        if not self.is_declared():
            return "공정이 선언되지 않았습니다"
        L = [f"{self.block or '(이름 없음)'} · {self.scale or '규모 미상'} · 지문 {self.fingerprint()}"]
        for k in sorted(self.answers):
            v = str(self.answers[k] or "").strip()
            if v:
                L.append(f"   {k}: {v}")
        if self.note:
            L.append(f"   메모: {self.note}")
        return "\n".join(L)


# ---------------------------------------------------------------- xlsx
def write_sheet(wb, onto, profile, card=None):
    """빈 공정 시트를 만든다. 행이 곧 질문이라 랩이 그대로 채운다."""
    ws = wb.create_sheet(SHEET)
    ws.append(["항목", "값", "왜 묻는가"])
    ws.append(["프로파일", profile, "이 표가 어느 제형의 것인지"])
    ws.append(["규모", (card.scale if card else ""), " / ".join(SCALES)])
    ws.append(["블록 이름", (card.block if card else ""),
               "같은 공정끼리 묶는 이름. 공정을 바꾸면 새 이름을 주세요"])
    ws.append(["선언자", (card.declared_by if card else ""), ""])
    ws.append(["선언일", (card.declared_at if card else ""), ""])
    for f in fields(onto, profile):
        for a in f["ask"]:
            key = f"{f['op']}.{a}"
            ws.append([f"{f['ko']} — {a}",
                       (card.answers.get(key, "") if card else ""),
                       "이 제형에서 " + " · ".join(f["because"]) + " 에 걸립니다"])
    ws.append(["메모", (card.note if card else ""), "그 밖에 남길 것"])
    return ws


def read_sheet(wb, onto=None, profile=None):
    """공정 시트 → Card. 시트가 없으면 빈 카드를 준다(옛 파일 호환)."""
    card = Card(profile=profile or "")
    if SHEET not in wb.sheetnames:
        return card
    ws = wb[SHEET]
    key_of = {}
    if onto is not None and profile:
        for f in fields(onto, profile):
            for a in f["ask"]:
                key_of[f"{f['ko']} — {a}"] = f"{f['op']}.{a}"
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or not row[0]:
            continue
        name = str(row[0]).strip()
        val = "" if len(row) < 2 or row[1] is None else str(row[1]).strip()
        if name == "프로파일":
            card.profile = val or card.profile
        elif name == "규모":
            card.scale = val
        elif name == "블록 이름":
            card.block = val
        elif name == "선언자":
            card.declared_by = val
        elif name == "선언일":
            card.declared_at = val
        elif name == "메모":
            card.note = val
        else:
            card.answers[key_of.get(name, name)] = val
    return card
