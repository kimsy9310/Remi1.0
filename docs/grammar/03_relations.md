# 03 술어 — 관계는 형식이 문법이고 값은 지식이다. 스코프는 사다리 한 줄이다

1차 2026-09-17 (S1). 규칙은 `RULES.en.md` C 절(C1~C9)에 이미 확정돼 있다. 이 장은 **재 본 것**과,
규칙이 요구하지만 아직 파일에 없는 **내용**(P.axes 8건 · IN 두 목록)의 초안이다. 도구:
`tools/scope_index.py`(신설, RULES C9).

---

## 현황 — 스코프 대장으로 재 봄 (2026-09-17)

`python tools/scope_index.py` — 지금 파일 꼴 그대로 읽되 옛 표기(점 스코프 · `universal`)를 정본
꼴로 바꿔 읽는다. 파일은 안 고친다.

| 무엇 | 수 |
|---|---|
| 성분 전부 | **378** = 재료 override 166 · 기능군 effects 79 · P.axes(PO) 70 · flavor_profile 50 · IN 13 |
| 제형 | 7 (ST 를 안 적은 6개는 `ST.ambient` 로 읽음) |
| 옛 표기를 바꿔 읽은 성분 | **106** — 이관표 #2 의 실제 크기 (C2 파일의 점 스코프 125곳 중 성분에 붙은 것) |
| 스코프별 | `any` 185 · 아이스크림 80 · 소스 40 · 음료 34 · 현탁액 33 · `SC.emulsion.ow` 6 |

불변식 다섯의 결과:

| 불변식 | 결과 | 뜻 |
|---|---|---|
| (i) 없는 스코프 | **0** | 별칭표로 바꾸면 모든 마디가 목록 값이다 |
| (ii) 고아 | **0** | 모든 성분이 제형 하나 이상에 맞는다 |
| (iii) 부호 반대 | **0** | 같은 (owner, to) 가 겹치는 스코프에서 부호가 다른 경우가 없다 — 아래 |
| (iv) 구멍 | **4** | dressing · dip 의 core 축 `L.tx.cling` `L.tx.thickness` |
| (v) 중복 | **1** | `ING.paprika_smoked → L.ar.smoky @ any` 두 번 |

### "반대부호 17건" 은 충돌이 아니었다

`session_split.md` 가 열린 일로 적은 "R-2 반대부호 17건" 을 (iii) 으로 찾으면 **0건**이다. 대신
RELATION 파일에서 부호가 음인 관계를 세면 R-1 `monotone: decreasing` **15** + R-2 `inverse_corr` **2**
= **17**. 즉 그 17건은 "점도가 오르면 흐름성이 내린다" 같은 **음의 방향**이지, 같은 관계가 스코프에
따라 부호를 바꾸는 충돌이 아니다. 새 어휘에서는 그냥 `direction: decrease` 다. **보류 #2 는 이것으로
닫힌다** — 판정할 것이 없다. (C9 (iii) 는 그대로 둔다; 앞으로 생길 진짜 반전을 잡는 자리다.)

### 구멍 4건은 B5-1 이 정확히 메운다

dressing 과 dip 은 소스에서 파생됐고, 걸쭉함·코팅성은 `P.apparent_viscosity → L.tx.thickness` 같은
P.axes 가 `SC.emulsion.ow` 스코프로 있지만 **재료 → P 엣지가 `SC.emulsion.ow|APP.sauce` 잎에만**
있어서 B5 로는 못 닿는다. 지금 정본 로더는 이것을 손으로 적은 `scopes` 집합(`SC.emulsion.ow.sauce`)
과 `add_application` 의 임시 필드 `dose_parent` 로 메워 왔다 — 둘 다 규칙 위반(B6). B5-1 대로 계산하면:

    dressing  ← sauce (판별 파라미터 범위 겹침 2.58, 성분 2개, 확신도 −1)
    dip       ← sauce (겹침 3.32, 성분 2개, 확신도 −1)

도구가 이 빌림을 표에 남긴다. 로더가 B5-1 을 구현하면(이관표 #25) `dose_parent` 와 손 목록은
없어진다.

### 중복 1건 → S2

`ING.paprika_smoked` 의 `L.ar.smoky` 성분이 `any` 스코프로 두 번 적혀 있다. INGREDIENT 는 S2 소유
— 보고만 한다.

---

## 1. P.axes — 옛 PO 를 P 안으로 접는다 (C3)

PO 70건은 그대로 P.axes 의 성분이 된다(`percept → axis`, `monotone → direction`). 접는 것 자체는
이관(#11). 이 장이 채워야 하는 것은 **`axes` 가 빈 P 8개의 내용**(보류 #3)이다. 아래는 초안이다 —
관능·식품 과학의 통설 범위에서 적었고, **확정 전에는 쓰지 않는다** (확신도는 전부 `medium` 이하).

| P | axis | direction | functional_form | scope | 근거 |
|---|---|---|---|---|---|
| `P.solid_fat_content_37C` | `L.tx.creaminess` | increase | saturating | `any` | 입 온도에서 남는 고체지가 크리미함의 지방감을 준다; 너무 높으면 왁시 |
| | `L.tx.melting` | decrease | linear | `SC.emulsion.ow\|APP.dessert\|ST.frozen` | SFC37 높을수록 입에서 덜 녹는다 |
| | `L.tx.mouthcoating_persistence` | increase | linear | `any` | 고체지가 코팅으로 남는다 |
| `P.Tg_serum` | `L.tx.hardness` | increase | linear | `…\|ST.frozen` | Tg′ 가 높을수록 같은 온도에서 더 단단 |
| | `L.tx.icy` | decrease | linear | `…\|ST.frozen` | Tg′ 가 높으면 재결정이 느려 얼음 씹힘이 준다 |
| `P.density_difference` | `L.ap.oil_ring` | increase | linear | `SC.emulsion.ow\|APP.beverage` | Δρ 가 클수록 크리밍이 빨라 목 고리가 생긴다 (Stokes) |
| | `L.ap.separated` | increase | linear | `SC.emulsion.ow` | 같은 기전, 소스에서는 분리로 보인다 |
| `P.flocculation` | `L.ap.separated` | increase | linear | `SC.emulsion.ow` | 응집체가 크리밍을 가속 |
| | `L.tx.thickness` | increase | saturating | `SC.emulsion.ow` | 응집 망이 점도를 올린다 (약한 겔) |
| `P.ostwald_ripening` | `L.ap.cloudy` | decrease | linear | `SC.emulsion.ow\|APP.beverage` | 방울이 굵어지면 탁도가 준다 |
| | `L.ap.oil_ring` | increase | linear | `SC.emulsion.ow\|APP.beverage` | 굵어진 방울이 크리밍 |
| `P.salt_in_water_phase` | `L.ta.salty` | increase | saturating | `any` | 짠맛은 수상 염농도를 따른다 (총량이 아니라) |
| `P.solids_volume_fraction` | `L.tx.thickness` | increase | saturating | `SC.suspension` | φ_s 가 오르면 점도가 급히 오른다 (Krieger–Dougherty) |
| | `L.tx.grittiness` | increase | linear | `SC.suspension` | 입자가 많을수록 꺼끌거림이 잘 느껴진다 (d90 과 함께) |
| `P.water_activity` | — | | | | **감각 축 없음.** 안전·보존 지표. `axes` 를 비워 두되 `constraint: true` 로 표시해 (iv) 검사에서 빼는 것이 맞다 — 09-13 에 "제약은 P 가 아니다" 라 했으나, 재는 것은 P 이고 제약은 제형 범위가 진다. 둘이 모순되지 않는다 |

**판단 1.** 위 15 성분과 `water_activity` 의 처리를 확정해 주시면 PO 레코드(지금 꼴)로 넣는다.

---

## 2. IN — 두 목록 (C4)

지금 13건을 나누면 인과 6 · 겹침 7 (01장 §4). 이관(#21) 때 `interactions` / `overlaps` 로 가른다.
내용 쪽에서 남는 질문은 **인과 목록이 충분한가**다. 관능과학이 확립한 것 중 지금 없는 것:

| from | to | direction | magnitude | scope | 근거 |
|---|---|---|---|---|---|
| `L.ta.sour` | `L.ta.sweet` | decrease | medium | `any` | 신맛–단맛 상호 억제 (있는 것은 단맛→쓴맛 뿐) |
| `L.ta.sweet` | `L.ta.sour` | decrease | medium | `any` | 같은 쌍의 반대 방향 |
| `L.ta.salty` | `L.ta.umami` | increase | medium | `any` | 소금이 감칠맛을 키운다 (MSG–NaCl 상승) |
| `L.ta.salty` | `L.ta.sweet` | increase | weak | `any` | 저농도 소금의 단맛 강화 |
| `L.ta.umami` | `L.ta.salty` | increase | weak | `any` | 감칠맛이 짠맛 지각을 키움 (감염 배합의 근거) |
| `L.tx.thickness` | `L.ta.sweet` | decrease | weak | `any` | 점도가 높으면 맛 방출이 느려 단맛이 줄어 보인다 (향도 같이 — `L.ar.*` 전체에 적으려면 DC 처럼 묶어야 하므로 보류) |

**판단 2.** 이 여섯을 더할지. C4 의 "불확실한 관계는 적지 않는다" 를 지켜 위 여섯은 교과서 수준의
것만 골랐다. 마지막 줄(점도→맛)은 향 전체에 걸려 성분 하나로는 안 되므로 넣지 않는 쪽을 권한다.

---

## 3. 규칙 → `RULES.en.md` C 절

C1 스코프는 성분에만 · C2 재료 엣지 · C3 P.axes · C4 IN 두 목록 · C5 DC · C6 LESSON · C7 RP ·
C8 KN 보류 · C9 스코프 대장 다섯 불변식. 이 장은 덧붙이지 않는다.

---

## 4. 검사

| 규칙 | 검사 | 상태 |
|---|---|---|
| C9 (i)~(v) | `tools/scope_index.py` | **있음** — 오늘 4 + 1 건 걸림, 위에 판정 |
| C3 | `axes` 빈 P 목록 | 도구가 참고로 출력 (8건) |
| B5-1 | 빌림 후보와 겹침 점수 | 도구가 (iv) 줄에 붙임 |
| `selfcheck_v2` 한 줄 | 불변식 다섯을 selfcheck 에 넣기 | 이관 때 (도구가 exit 1 을 돌려주므로 지금도 CI 로 쓸 수 있다) |

---

## 5. 판단

1. §1 의 P.axes 초안 15 성분 + `water_activity` 처리 (`constraint: true` 로 (iv) 제외).
2. §2 의 IN 인과 여섯 추가 여부.
3. `ING.paprika_smoked` 중복 → S2 에 보고 (S1 이 안 고침).
4. 보류 #2 (반대부호 17) 는 닫음 — `RULES.en.md` Deferred 표에서 지울지.
