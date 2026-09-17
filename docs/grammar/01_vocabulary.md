# 01 어휘 — 이름공간은 열, 한 개념에 이름 하나

5차 2026-09-13 (S1). §12 의 일곱이 확정됐다. 4차에서 3차 피드백 9항목 반영 — §0(L·P 뜻 바로잡음) §2(수치 무게) §4(IN 두 종류) §6(LESSON 관찰 레코드) §7(RP 는 처방) §8(카드는 저장층이 아니라 보기) §9(스코프 대장). 규칙은 §10.
확정된 것: `axis` · 이관 한 번에 · 죽은 이름은 지운다 · KN 은 지금 논의하지 않는다.

---

## 0. 그림 — 바뀐 것

**L 과 P 의 뜻 — 바로잡음 (09-13).** 앞 판에서 P 를 "물성" 이라 불렀는데, 한국 식품 현장에서
물성은 식감(texture)을 뜻하므로 L.tx 와 헷갈린다. 정확히는:

    L.*   사람이 느끼는 것 전부의 낱말 — 맛 · 향 · 식감 · 외관 · 화학감각. 식감 낱말(걸쭉함 ·
          크리미함)도 L 이다. 관능 언어(lexicon).
    P.*   그 감각 중 일부를 **실험실에서 잴 수 있는 지표**(parameter) — 점도계의 점도, pH 미터의 pH.
          L 없이 P 만으로 제품을 말하지 않는다.

재 보니 P 39개 중 8개는 지금 **`PO.` 레코드가 없다** (`P.water_activity` `P.salt_in_water_phase`
`P.solids_volume_fraction` `P.solid_fat_content_37C` `P.Tg_serum` `P.density_difference`
`P.flocculation` `P.ostwald_ripening`). 4차 초안에서 "어느 L 과도 관계없다" 고 적었는데 틀렸다
(09-13 피드백) — 관계가 없는 것이 아니라 **적히지 않은 것**이다. SFC37 → 크리미함·녹는 성질,
Δρ → 크리밍 → 기름 고리, 오스트발트 → 탁함, Tg → 단단함·얼음 씹힘, 수상염도 → 짠맛. 채우는
자리는 **03장(술어) — PO 를 P.axes 로 접을 때**다. 접는 도구가 `axes` 가 빈 P 를 그대로 보여 주고,
S1 이 관계를 적는다. 여기서는 손대지 않는다.

**제약은 P 가 아니다 (09-13 결정).** 재료의 상·하한은 `ING` 의 `limitations` · 팔레트 범위(S2)에,
제품 수준 안전선(pH ≤ 4.6, aw)은 제형의 파라미터 **범위**에 이미 산다. P 자체에 `role` 을 두지
않는다 — P 는 전부 "잴 수 있고 어느 L 에 닿는 지표" 하나의 뜻이다.

2차 그림은 재료 → P → L 한 줄이었다. 피드백으로 축이 바뀌었다: **L 이 필수이고 P 는 보조다.**

```
   재료 · 기능군                          감각 (축)
   ING.*  (FT.* 역할 묶음)  ────────▶   L.*  ◀────▶  L.*
                  INGREDIENT 엣지           R-2 (IN.*)
                  "넣으면 이 감각들이            "느낌이 느낌을 바꾼다"
                   이렇게 움직인다"
                                            ▲
                          P.*  측정 지표 ──────┘  보조. 있으면 확신이 오르고,
                               (이름·단위·측정법·   없어도 돈다.
                                관계된 L 을 한 몸에)

   DC.*   "깊은 맛" = L 여럿의 묶음                      (관용어 분해)
   KN.*   시간이 가면 어떻게 변하나                        (지금 논의 안 함)
   ─────────────────────────────────────────────────────────
   제형(profile) = SC × APP × ST   — 제품을 정하는 프로파일 **넷 중 하나** (02장)
   scope          위 화살표(엣지 · IN)에 붙는 꼬리표: "이 제형에서 참"
   ─────────────────────────────────────────────────────────
   카드            축 × 맥락 마다 "어떻게 읽나"  (§8)
   LESSON · RP     문장. 기록인가 변수인가 — §6 §7
```

세 종류: **사물**(ING FT L P SC APP ST) · **화살표**(엣지 IN DC KN) · **문장**(LESSON RP).
`PO.` 는 P 안으로 접힌다(§1). `SA.` `IX.` 는 지운다(§9 → 00장 이관표).

---

## 1. P 는 보조 지표 — 재 본 것과 설계

**재 본 것 (2026-09-12).**

| 사실 | 수치 |
|---|---|
| 재료 → L 직접 엣지 | 기능군 24 + 재료 override 94 + flavor_profile 50 = **168** |
| 재료 → P 엣지 (P → L 은 PO 70건이 잇는다) | 기능군 55 + override 72 = **127** |
| 로더 규칙 | **직접 L 엣지가 이기고**, P 경유는 직접 엣지가 없을 때만 (`effects_of`, RULE 3) |
| 실측 P 를 읽는 코드 | 데이터 틀에 `instrumental` 시트(점도·Brix·pH·탁도)가 있으나 **선택**이고, 실측 12행 중 값은 pH 1건. 확신도에 반영하는 코드 없음 |

즉 지금도 시스템은 **실측 P 없이 돈다.** P 가 하는 일은 두 가지이고 둘 다 사전 지식이다:

    (a) 다리   재료→P 엣지 + P→L(PO) 을 합성해 재료→L 사전값을 만든다. 에멀전 식감·외관은
               거의 이 길로만 닿는다 (F6)
    (b) 측정   틀은 있으나 아무것도 안 한다

**설계 (제안).**

- **P 레코드 = 이름 · 단위 · 측정법 · 관계된 L.** 지금 `PO.*` 70건이 따로 있는 "P → L" 을 P 항목
  안으로 접는다. `PO.` 이름공간이 사라진다.

      - id: P.apparent_viscosity
        label: apparent viscosity
        unit: Pa.s @ 50 1/s
        method: {method: rotational rheometer / flow cup, cost_tier: cheap}
        axes:                                   # 옛 PO.*
        - {axis: L.tx.thickness, direction: increase, functional_form: linear, scope: any, confidence: high}
        - {axis: L.tx.body,      direction: increase, functional_form: saturating, scope: any, confidence: medium}
        - {axis: L.tx.cling,     direction: increase, functional_form: linear, scope: SC.emulsion.ow|APP.sauce, confidence: medium}

- **L 밑으로 내리나?** 한 P 가 여러 L 에 걸리고(점도 → 걸쭉함·바디·코팅), 한 L 이 여러 P 를
  가진다(크리미함 ← 지방분율·d32·점도). 나무가 아니라 그물이라 P 를 L 의 자식으로 둘 수 없다.
  대신 **L 쪽에 계산된 역방향 보기** `proxies: [P.…]` 를 두면 "이 감각을 재고 싶으면 무엇을 재나"
  가 L 에서 바로 보인다. 원본은 P 에만 적는다.
- **없어도 돈다 = 재료→L 직접 사전값이 모든 core 축에 있어야 한다.** (a) 의 합성 결과를
  도구가 **재료→L 직접 엣지로 실체화**(confidence 한 단 낮춰)하면, 런타임은 P 를 몰라도 되고
  P 는 순수 보조가 된다. 지금 F6 자리 — P 경유로만 닿는 core 축 — 가 그 도구의 대상이다.
- **있으면 확신이 오른다 = E1 의 일.** 실측 P 가 오면 그 P 의 `axes` 에 걸린 L 추정의 confidence
  를 올리고, 재료→P 엣지의 세기를 갱신한다. 문법은 자리만 정한다: 실측 P 는 Output 6/8 의
  `instrumental` 블록, 필드는 `{parameter, value, unit, sample_id}`.

---

## 2. ING 와 FT — 지금 관계와 설계

**재 본 것.** 기능군 42 · 재료 177. 그중 **별칭 hack** 이 기능군 18 · 재료 59 — `FT.fat_source_beverage_scope`
처럼 "같은 기능군인데 다른 스코프의 엣지를 더하려고" 만든 가짜 항목이다(로더 RULE 1 이 본체로
접는다). 진짜 재료 118 개의 기능군 수:

    기능군 0개  10       1개  41       2개  33       3개  22       4개  10       5개  1       6개  1

**57% 가 둘 이상**이다. `ING.gochujang` 은 여섯(fermented_paste · pungent_principle · colorant ·
umami_source · sweetener · particulate). 기능군 사이 계층은 `specializes` 1건(milk_protein → protein)
뿐이고, 엣지 없는 기능군이 둘(`FT.flavorant` 36개 재료 · `FT.preservative`).

관계의 실제 모양:

    FT   = 역할(role). "이 일을 하는 재료들" 의 묶음이지 분류 트리가 아니다
    ING  = 역할의 집합 + 자기만 다른 것(overrides)
    엣지 = 기능군에 적힌 것을 재료가 물려받고, override 가 덮는다   (2-tier)

문제는 **역할에 무게가 없다**는 것이다. 고추장은 sweetener 이긴 하지만 설탕처럼 sweetener 는
아니다. 지금은 여섯 역할의 엣지를 모두 같은 세기로 물려받는다.

**설계 (제안).**

- **FT 는 트리가 아니라 역할 집합.** 계층은 `specializes` 로만 (protein → milk_protein · plant_protein;
  thickener → gum · starch). 상속은 위로 한 단.
- **재료의 역할에 무게를 붙인다.** 주기능/부기능 둘로 가르지 않고 세기 세 단:

      - id: ING.gochujang
        functions:
        - {function: FT.pungent_principle, weight: strong}
        - {function: FT.umami_source,      weight: medium}
        - {function: FT.sweetener,         weight: weak}
        - {function: FT.colorant,          weight: strong}
        - {function: FT.particulate,       weight: medium}

  물려받는 엣지의 세기 = 기능군 엣지 세기 × 역할 무게 (S3 가 곱을 정한다). `overrides` 는 그대로.
- **별칭 hack 77건은 스코프 트리(02장)가 서면 없어진다.** 스코프별 엣지는 기능군 안에 `scope`
  를 달아 나란히 적으면 되기 때문이다.

**수치 무게로 가는 길 (09-13 질문: "나중에 +2.4 처럼 수치화될 수 있나, 지금 방식이 가장 싼가").**
가능하고, 지금 방식이 가장 싸다 — 이유는 이미 문자열이 숫자이기 때문이다. 정본 로더:

    MAGNITUDE  = {weak: 0.3, medium: 0.6, strong: 1.0}     # ±3 척도에서 1 SD 당
    CONFIDENCE = {high: 8.0, medium: 2.0, low: 0.4}        # 사전 정밀도 Λ

즉 `strong` 은 `1.0` 의 별명이다. 규칙 하나만 더하면 끝난다: **세기 필드는 세 단어 중 하나이거나
숫자다.** 단어면 표로 바꾸고 숫자면 그대로 쓴다. 학습(E1)이 낸 값은 숫자로, `source: {kind:
measured}` 와 `confidence` 를 달고 되돌아온다. 스키마가 안 바뀌므로 비용은 로더 한 줄이다.

단, **숫자가 되돌아오는 자리는 역할 무게가 아니라 §3 의 재료→L 엣지다.** 실험이 재는 것은
"고추장 1% 당 매운맛 몇 칸" 이지 "고추장의 pungent 역할 몇 배" 가 아니다. 역할 무게는 사전값이라
세 단어면 충분하고, 수치는 엣지에 쌓인다 — 피드백에서 스스로 이르신 결론과 같다. 숫자의 단위는
04장이 정한다(통상량을 넣었을 때 ±3 척도에서 움직이는 칸 수).

---

## 3. INGREDIENT 엣지 — "재료가 움직이는 L 의 집합"

새 이름공간을 만들지 않는다. 재료(또는 기능군) 항목 **안의 목록**이다. 대상은 원칙적으로 L 이고,
P 를 대상으로 적은 것은 §1 의 다리다.

방향·세기를 적는 법 — 지금 세 벌이 있다:

| 어디 | 방향 | 세기 |
|---|---|---|
| 기능군 effects · override | `direction: increase/decrease` | `magnitude: weak/medium/strong` |
| flavor_profile | `direction` | **`intensity`** |
| R-1 (PO) | **`monotone: increasing/decreasing`** | (없음 — functional_form) |

한 벌로: **`direction` + `magnitude`**, 선택으로 `functional_form`(문턱·포화) 과 `scope`. 부호를
따로 두지 않는다 — `decrease` 가 부호다.

    effects:
    - {axis: L.tx.thickness, direction: increase, magnitude: strong, scope: SC.emulsion.ow|APP.sauce,
       functional_form: saturating, confidence: high, source: {kind: prior, date: 2026-08-18}}

집합의 원소 하나 = 축 하나. 같은 축이 두 스코프에 있으면 두 원소다(잎이 이긴다, 02장).

**부정 효과도 여기 (09-13 확인).** 꼴은 이미 그렇다 — `direction: decrease` 엣지가 53건 있고
override 는 기능군과 무관한 축을 더할 수 있다. 내용은 아직 아니다: `ING.gochujang` 을 조미 스코프에서
풀어 보면 축 16개가 전부 **증가**다(umami · 장 향 · 매운맛 · 색 · 짠맛 · 바디 · 단맛 · 꺼끌거림 …).
"신선함 −1.2" 같은 부작용 엣지는 한 건도 없다. 꼴은 S1 이 정했고 채우는 것은 S2 의 일이며,
§1 의 실체화 도구가 "한 재료가 움직이는 L 전부" 를 한 표로 뽑아 주면 빈 곳이 보인다
(`data/ingredient_axis_map.xlsx` 가 그 표의 전신).

---

## 4. IN — L ↔ L. 작게 두는 것이 맞다

13건. 피드백: *"모든 L–L 을 규명하는 건 비효율적이고, 확실한 것만 적으면 몇 개 없고, 불확실한
것까지 적으면 오류가 크다."* 맞다. 그래서 IN 은 **작게 두는 층**이고 그것이 결함이 아니다.

**왜 작아도 되나.** L 끼리 같이 움직이는 것 대부분은 **같은 원인** 때문이다 — 지방을 올리면 크리미함
과 바디가 같이 오르는 것은 지방→크리미함, 지방→바디 두 엣지가 이미 말한다. 그런 것은 IN 에 적으면
이중 계산이다. IN 에 남는 것은 원인을 빼고도 남는 **감각 수준의 상호작용**뿐이며, 관능과학이 확립한
것은 몇 안 된다 — 맛끼리의 억제(짠맛→쓴맛, 단맛→쓴맛 · 신맛), 온도→단맛, 향→맛 강화(바닐라→단맛),
맛→향 강화(단맛→과일 향). 열 몇 개면 다 적는다. **불확실한 것은 적지 않는다** — 없어도 모형은 돌고,
있으면 목표 이동(R-3)이 조금 더 맞는다. P 와 같은 원리다.

**"인과만" 의 뜻과 상관 7건.** 지금 13건을 나누면:

| 종류 | 건 | 예 | 무엇에 쓰나 |
|---|---|---|---|
| 인과 `enhance` `suppress` | 6 | 저온→단맛 억제 · 짠맛→쓴맛 억제 · 바닐라→단맛 강화 | **R-3 목표 이동.** "덜 달게" 목표를 실제 당량으로 옮길 때 |
| 상관 `pos_corr` `inverse_corr` | 7 | 매끄러움~얼음 씹힘(역) · 흐름성~걸쭉함(역) · 크리미함~바디(정) · 코팅 잔류~뒷맛 길이(정) | **"둘 다 core 로 두지 마라"** — 목적함수 이중 계산 방지. 주석이 전부 그렇게 적혀 있다 |

둘은 같은 필드에 있을 뿐 **다른 일**을 한다. 상관 7건은 원인이 하나(얼음 결정 크기, 점도, 지방)라
그 원인의 엣지·P.axes 가 이미 둘을 움직이고, IN 의 역할은 B1 SCOPE 가 목표를 고를 때 "겹친다" 고
알리는 것이다. 그러므로:

**설계.** IN 을 두 목록으로 가른다 — 같은 원소 꼴, 다른 이름과 용도.

    interactions:   [{from, to, direction, magnitude, scope}]      인과. R-3 가 읽는다
    overlaps:       [{axes: [L.a, L.b], scope, why}]                겹침. B1 SCOPE 가 읽는다 ("둘 다 core 금지")

`effect` 필드는 사라지고 `direction` 이 부호를 진다(`suppress` = `decrease`). "반대부호 17건" 은
이 정리 뒤 03장에서 본다 — 그 17건이 인과인지 겹침인지부터.

## 5. DC — 관용어 = L 의 집합

6건. "깊은 맛" = umami(strong) + kokumi(medium) + caramel(medium) + aftertaste(weak). 사용자 말(S4)이
렉시콘에 없는 관용어일 때 여기로 푼다.

엣지와 같은 집합 형식으로 간다. 원소 = {axis, direction, magnitude}. "밍밍하다" 는 umami **decrease**
이므로 방향이 필요하다 — 지금 `weight` 만 있고 방향이 없어 "밍밍하다" 와 "깊은 맛" 이 같은 축
집합으로 보인다.

    - id: DC.0002
      label: flat / watery-tasting
      ko: 밍밍하다
      components:
      - {axis: L.ta.umami, direction: decrease, magnitude: strong}
      - {axis: L.ta.salty, direction: decrease, magnitude: medium}

---

## 6. LESSON — 관찰 레코드. 정의한 어휘로 쓰고, 사람 말로도 쓴다

19건, 제형 항목의 `constraints` 안. 코드는 읽지 않는다. 3차 초안은 "변수 옆 `why` 로 흩어 넣자" 였고,
피드백은 **별도 공간으로 두되 세분화하자** — "어느 제형에서 어느 재료가 어떻게 움직였고 어떻게
쓰여서 이 교훈이 나왔는지를 정의한 어휘로 적고, 사람 말로도 적고, RP 가 변수로 쓸 때 근거가 되게."
그 구조가 맞다. 세분화하면 LESSON 은 **관찰 레코드**가 된다:

    - id: LESSON.sugar_triple_role
      type: reformulation_dependency            # 8 타입 그대로
      scope: SC.emulsion.ow|APP.dessert|ST.frozen
      about: {ingredient: ING.sucrose}          # 무엇에 대한 관찰인가 (재료 · 기능군 · 파라미터)
      observed:                                  # 정의한 어휘 — §3 과 같은 원소 꼴
      - {axis: L.ta.sweet,    direction: increase, magnitude: strong}
      - {axis: L.tx.body,     direction: increase, magnitude: medium}
      - {axis: L.tx.hardness, direction: decrease, magnitude: strong}   # 빙점강하
      when: {dose: "12-16% w/w", process: "batch freezer, -5C draw"}     # 선택
      statement: 설탕은 빙점강하 · 바디 · 단맛을 한꺼번에 진다. 줄이면 셋을 따로 보상해야 한다.
      source: {kind: expert, date: 2026-08-18}
      confidence: medium

두 절반이 각각 할 일이 있다:

| 절반 | 누가 읽나 | 무엇을 하나 |
|---|---|---|
| `observed` (어휘) | 검사 · RP | **엣지와 대조한다.** observed 의 원소가 §3 엣지 집합에 없으면 "관찰은 있는데 변수가 없다" 로 걸린다 — 19건 중 2건이 지금 그 상태(§6 이전 표). 있으면 그 엣지의 근거가 된다 |
| `statement` (사람 말) | C4 · D4 · 사용자 | "왜" 를 말한다 |

**비용.** 19건 × 구조화 한 줄. observed 원소 꼴이 엣지와 같으니(V7) 도구가 "이 LESSON 이 말하는
엣지가 있나" 를 자동으로 검사하고, 없으면 **엣지 초안을 제안**할 수 있다. 관찰 → 변수 승격의
경로가 그렇게 생긴다. 이보다 싼 구조는 없다고 본다 — 사람 말만 두면 검사가 안 되고, 어휘만 두면
"왜" 가 사라진다.

**언제 LESSON 이 생기나.** 세 경로: 문헌·전문가(지금 19건), 실험 결과에서 D4 가 "예상과 달랐다"
를 발견했을 때(E1 이 관찰 레코드를 남김), 사용자가 화면에서 적을 때(C0 공정 메모처럼).

## 7. RP — 재배합 패턴

2건, `layerC2_ext_reformulation.yaml`, v1 로더만 읽는다.

    RP.low_sugar_ice_cream
      target:        설탕을 줄이면서 단맛 · 바디 · 떠짐을 지킨다
      compensation:  [ING.polydextrose, ING.sugar_alcohol, ING.high_intensity_sweetener]
      rationale:     설탕의 세 역할을 세 재료로 나눈다 (LESSON.sugar_triple_role)

**이것이 무엇인가.** C4 Gap-fill 의 **답을 미리 적어 둔 것**이다. C4 는 원리상 계산이다 — 재료 X 를
줄이면 X 의 엣지가 걸린 축들이 지지를 잃고, 그 축에 직접 엣지를 가진 다른 재료·기능군을 스코프
안에서 찾으면 된다. RP 는 그 검색의 전문가 사전값(prior)이다: 검색이 후보를 여럿 낼 때 무엇을
앞세울지, 셋을 **같이** 넣어야 한다는 결합 지식(단독 검색으로는 안 나오는 것).

**필요한 어휘.** 새 사물은 없다. 필요한 것은 레코드 꼴뿐이다:

    - id: RP.<이름>
      scope:       SC.emulsion.ow|APP.dessert|ST.frozen
      reduce:      {ingredient: ING.sucrose}              # 또는 function: FT.sweetener
      keep:        [L.ta.sweet, L.tx.body, L.tx.hardness]  # 지킬 축
      compensate:                                         # 순서 = 함께 넣는 묶음
      - {ingredient: ING.polydextrose,             restores: [L.tx.body]}
      - {ingredient: ING.sugar_alcohol,            restores: [L.tx.hardness]}
      - {ingredient: ING.high_intensity_sweetener, restores: [L.ta.sweet]}
      why:         설탕은 세 역할을 한꺼번에 진다 …
      confidence:  medium

`target` · `compensation` · `rationale` 은 이 꼴로 바뀐다. `why` 는 LESSON id 목록(`evidence: [LESSON.sugar_triple_role]`)이 된다.

**LESSON 과의 관계 — 이해 확인 (09-13).** "RP 는 LESSON 의 수치화 · AI 가 읽는 판, LESSON 은 사람
말" 은 반쯤 맞다. 정확히는 **말하는 종류**가 다르다:

    LESSON   관찰  "설탕을 줄였더니 셋이 무너졌다"        — 사실. observed(어휘) + statement(사람 말)
    RP       처방  "설탕을 줄이려면 셋을 이렇게 넣어라"   — 행동. reduce/keep/compensate(어휘) + why(사람 말)

둘 다 어휘 절반과 사람 말 절반을 가진다. **수치는 어느 쪽에도 살지 않는다** — 수치는 §3 엣지에
쌓이고(학습이 갱신), RP 는 그 엣지를 가리킬 뿐이다. 그래야 실험이 한 번 더 쌓였을 때 RP 를 다시
쓰지 않아도 처방의 숫자가 따라온다. **정의할 필요성:** C4 가 P 처럼 "없어도
돌고 있으면 좋아지는" 보조 지식이라, 규칙은 하나면 된다 — *RP 가 없어도 C4 는 검색으로 답하고,
RP 가 있으면 그 답을 앞세운다.* 소유는 재료를 들고 있으니 S2.

---

## 8. 카드 — 저장하는 층이 아니라 합쳐서 보여 주는 보기(view)

피드백: *"보편 카드는 필요 없어 보인다. 제품 카드 밑에 축 카드가 들어가는 게 맞고, 축 카드가 필요한지도
의문이다. 깊게 들어가자."*

**재 본 것 (09-13).**

| 사실 | 수치 |
|---|---|
| 제형 카드 | 7파일 106장 (+ 보편 6장). 전부 `ko.anchors` 를 가짐 |
| 제형 고유 내용 (평가 주의 `evaluation_note`) | **35장** — 나머지 71장은 tier · goal · 템플릿 앵커뿐 |
| 여러 제형에 같은 축 | 24축, 그중 **14축은 어느 제형에서나 내용이 같다** (복사본) |
| 같은 사실을 두 곳에 | 제형 파일 `relevant_attributes`(tier · goal 96건) 와 카드의 tier · goal — **16건 어긋남** |

즉 카드 106장 중 "이 제형에서 다르게 읽어야 한다" 는 정보는 35장 분량이고, tier·goal 은 제형 파일에
이미 있으며 둘이 벌써 갈라졌다. 카드가 **별도 저장층**이라서 생긴 표류다.

**설계 — 카드는 세 곳의 사실을 합쳐 만드는 보기다. 저장하지 않는다.**

    L.*  (렉시콘)             기본값: 앵커 템플릿("기준보다 뚜렷하게 덜/더 {label}") · tier monitored · goal maintain
      ▲ 덮는다
    제형 항목 relevant_attributes   이 제형에서: core 인가 · goal · evidence_required · 평가 주의(35건이 여기로)
      ▲ 덮는다
    PRODUCT_CARD                이 제품에서: 정체성 축 · tier/goal 바꾼 것 · 뺀 축 · 실측 열 · 제품 주의

    = 축 카드 (product, axis) — 화면과 엔진이 보는 것. 파일로 두지 않는다.

이렇게 하면: **보편 카드 파일이 없어진다**(L 의 기본값이 그 일을 한다 — 소금은 어디서나 짜다).
**축 카드 파일이 없어진다**(제형 파일의 축 목록에 평가 주의 한 필드가 더해질 뿐이고, tier·goal 이중
저장이 사라진다). **제품 카드만 남는다.** 카드는 "합성 결과" 라는 뜻으로만 쓰는 말이 된다.

**제품 카드 밑에 축 카드를 넣자는 안과의 차이.** 그렇게 하면 제형 수준의 평가 주의("아이스크림은
먹는 온도에서 평가하라", "바디감을 먼저 크리미함을 나중에")가 제품마다 복사된다 — 09-11 에 재 보니
제품 카드 16장 중 8장이 복사본이었던 그 문제다. 제형 수준 정보는 제형에 한 번만 있어야 한다. 다만
그것을 **별도 카드 파일**로 둘 이유는 없다 — 제형 항목 안이면 된다. 결론은 사용자 안의 절반이다:
파일로서의 축 카드는 없애고, 내용은 제형으로 흡수한다.

**두 가지 정보의 분리** (피드백의 "사용자의 제품 정보 vs AI 가 받아들일 학습 정보"): 제품 카드는
**사용자의 제품 정보**만 든다. 학습 정보(재료가 축을 얼마나 움직였나)는 제품 카드에 들어가지 않고
§3 엣지로 간다 — 09-10 결정 "좌표는 격리하고 기울기는 공유한다". 그래서 제품 카드가 길어질 일이
없다: 정체성 축 2~3 · 바꾼 것 몇 줄 · 실측 열 매핑.

**"보기(view)" 와 "저장하지 않는다" 의 뜻 — 예 하나로 (09-13 질문).** 쌀음료에서 단맛 축을 화면에
띄운다고 하자. 지금은 그 카드가 `layerM_cards_beverage.yaml` 에 **한 장으로 저장**되어 있다.
새 방식에서는 세 파일에 **조각**만 저장되고, 카드는 읽을 때 조각을 포개서 만든다:

    ① 렉시콘  L.ta.sweet            anchors: {-3: 기준보다 뚜렷하게 덜 달다, 0: 기준과 구분되지 않는다, +3: … 더 달다}
                                    tier: monitored   goal: maintain          ← 모든 제형·제품의 기본값
    ② 제형    beverage 의 축 목록     L.ta.sweet: {tier: core, evaluation_note: 마시는 온도에서 평가. 차가우면 단맛이 눌린다}
    ③ 제품    RV_rice_milk 제품 카드  L.ta.sweet: {legacy_column: sens_sweet}

    = 카드   (RV_rice_milk, L.ta.sweet)
             anchors ①  tier core ②  goal maintain ①  evaluation_note ②  legacy_column ③

이 "=" 아래 것이 화면과 엔진이 보는 카드다. **파일에는 없다** — `V2Ontology.load_cards` 가 ①②③ 을
읽어 그 자리에서 만든다(지금도 제품 카드는 이렇게 합성한다 — `_compose_product_cards`. 그 합성을
①② 까지 내리는 것뿐이다). "저장하지 않는다" 는 카드를 잃는다는 뜻이 아니라 **한 사실을 한 곳에만
둔다**는 뜻이다: 단맛 앵커는 ① 한 곳, 음료에서 core 라는 것은 ② 한 곳, 실측 열 이름은 ③ 한 곳.
지금은 tier 가 ② 와 카드 파일 두 곳에 있어 16건이 갈라졌다 — 두 곳에 있으면 반드시 갈라진다.

무엇이 바뀌나:

| 누가 | 지금 | 새 방식 |
|---|---|---|
| 패널 (화면) | 카드를 본다 | 똑같은 카드를 본다 — 차이 없음 |
| 엔진 | 카드에서 core 축·goal 을 읽는다 | 합성된 카드에서 읽는다 — 차이 없음 |
| S1 (저자) | 아이스크림에서 단맛 읽는 법을 바꾸려면 카드 파일을 고친다 | 제형 항목의 축 한 줄을 고친다. 앵커 문구를 바꾸려면 렉시콘 한 곳 |
| 제형을 새로 낼 때 | 카드 파일 복사 (오늘 `add_application` 이 한 일) | 복사할 것이 없다 — 축 목록만 적는다 |

축 카드가 필요한가에 대한 답: **개념으로는 필요**(화면이 보여 주는 그것), **저장 단위로는 불필요**.

카드(보기)의 어휘는 그대로: `axis` `tier` `goal` `method` `scale_type` `anchors` `evidence_required`
`confidence` `evaluation_note` `pitfalls` `legacy_column`. `active_in` 은 사라진다.

## 9. 스코프 — 다시 설명, 그리고 어디에 붙나

**무엇인가.** 어떤 문장이 참인 **범위**다. "잔탄검을 넣으면 걸쭉해진다" 는 소스에서 strong,
음료에서 medium, 아이스크림에서는 걸쭉함이 아니라 얼음 재결정을 막는 일을 한다. 문장 하나에
제형이 붙어야 참·거짓이 정해진다. 그 제형 표시가 스코프다.

**꼴.** 제형과 같은 세 축이다 — `SC|APP|ST` — 단, 상위 노드로 넓게 잡을 수 있다:

    any                                   모든 제형에서 참 (소금은 짜다)
    SC.emulsion.ow                        모든 O/W 에멀전에서 참 (기름 많으면 크리미)
    SC.emulsion.ow|APP.sauce              소스와 그 하위(드레싱·딥)에서 참
    SC.emulsion.ow|APP.dessert|ST.frozen  아이스크림에서만 참

넓은 스코프의 문장을 좁은 제형이 **물려받고**, 좁은 스코프의 문장이 있으면 **그것이 이긴다.**
02장의 트리가 "무엇이 무엇의 상위인가" 를 정한다. 지금 정본 로더가 손으로 든 `scopes` 집합은
그 계산 결과를 미리 적어 둔 것이고, 손으로 적어서 빠뜨린 것이 09-10 의 아이스크림 사고였다.

**지금 어디에 붙어 있나 — 여섯 자리.**

| 자리 | 지금 필드 | 정말 필요한가 |
|---|---|---|
| INGREDIENT 엣지 (245건) | `scoped_to_structure_class` | **필요.** 재료 효과는 제형을 탄다 (잔탄) |
| R-1 PO (70건) | `scope` | 필요 — §1 에서 P.axes 로 접히며 따라간다 (꺼끌거림 문턱은 현탁액) |
| R-2 IN (13건) | `scope` | **필요.** 저온→단맛 억제는 언 것에서 |
| KN | `scope` | 보류 |
| 축 카드 (112장) | `active_in` | **불필요.** 카드는 제형 파일 안에 산다 — 파일이 곧 스코프 |
| PARAMETER (3건) | `scope: universal` | **불필요.** 측정 지표 자체는 스코프가 없다. 그 P 의 `axes` 원소가 `any` 를 가지면 된다 |

**설계.** 스코프는 **문장(화살표)에만** 붙는다 — 엣지 · P.axes · IN. 사물(L P ING FT)과 카드에는
붙지 않는다. 필드 이름은 `scope`, 없으면 `any`. 표기는 파이프 하나.

이렇게 하면 "어디에 붙나" 의 답이 한 줄이 된다: **참·거짓이 제형에 따라 달라지는 문장에.**

---

**스코프 오류를 어떻게 찾나 (09-13 질문).** 스코프는 문장에만 붙고 문장은 세 파일(엣지 · P.axes · IN)
에 흩어져 있다 — 그래서 **찾는 것은 사람이 아니라 도구**여야 한다. 스코프의 어휘가 유한하고(트리
노드의 조합), 붙는 자리가 셋뿐이면(V6) 도구가 **모든 문장을 한 표로** 뽑을 수 있다:

    scope index (스코프 대장)   한 줄 = 문장 하나
    layer · id · from · to · direction · magnitude · scope · 덮는 제형들 · 파일:행

`tools/audit_axis_scope.py` 가 이미 제형 × 축 표를 만들고 있으니 그 앞단이다. 오류는 그 표 위의
**불변식 넷**으로 잡힌다:

| 오류 | 불변식 | 예 |
|---|---|---|
| 없는 스코프 | 스코프 문자열의 모든 단이 트리 노드다 | `SC.frozen.ice_cream` — SC 트리에 없음 |
| 고아 문장 | 스코프가 덮는 제형이 하나 이상이다 | 제형을 뺐는데 그 스코프 엣지가 남음 (오늘 soup 을 빼면서 생길 수 있었던 것) |
| 모순 | 같은 (from, to) 가 **겹치는** 스코프에서 부호가 다르면, 좁은 쪽에 `why` 가 있어야 한다 | "반대부호 17건" — 의도(유화제 역할 반전)인지 실수인지 |
| 구멍 | 제형의 core 축마다 그 제형을 덮는 재료→L 문장이 하나 이상이다 | 아이스크림에 짠맛 문장 없음 |

넷 다 계산이다. 사람은 표를 읽지 않고 **걸린 줄만** 본다. 이것이 스코프를 문장에 흩어 두어도 되는
조건이고, 반대로 이 대장이 없으면 흩어 두면 안 된다. → `tools/scope_index.py --check` 신설(S1),
`selfcheck_v2` 에 불변식 넷.

## 10. 규칙

**V1 — 이름공간은 열.**

| 접두 | 종류 | 층 | 세션 | 파일 |
|---|---|---|---|---|
| `L.` | 사물 · 감각 축 | LEXICON | S1 | `layerL_lexicon.yaml` |
| `P.` | 사물 · 보조 지표 (관계된 L 포함, 옛 `PO.`) | PARAMETER | S1 | `layerA_parameters.yaml` |
| `SC.` `APP.` `ST.` | 사물 · 제형의 세 축 | STRUCTURE | S1 | `layerS_taxonomy.yaml`(트리) · `layerS2_profiles.yaml`(조합) |
| `ING.` `FT.` | 사물 · 재료 · 역할 | INGREDIENT | S2 | `layerC2_*.yaml` |
| `IN.` `DC.` | 화살표 · 감각↔감각 · 관용어 분해 | RELATION | S1 | `layerR_seed.yaml` |
| `KN.` | 화살표 · 시간 | RELATION | S1 | 보류 |
| `LESSON.` | 문장 · 관찰 레코드 (어휘 + 사람 말) | STRUCTURE | S1 | `layerS2_profiles.yaml` → 별도 목록 |
| `RP.` | 문장 · 처방 (보상 사전값) | INGREDIENT | S2 | `layerC2_ext_reformulation.yaml` |

없어지는 것: `PO.`(P 로 접힘) · `SA.` `IX.`(지움). 엣지는 접두 없이
항목 안에 산다.

**V2 — ID 는 `접두.영어_소문자`.** 낱말 `_`, 계층 `.`. `IN` `DC` `KN` `RP` 만 번호 또는 이름 —
번호(`IN.0001`) 로 통일. ID 에 한글 없음.

**V3 — `SC.` 뒤에는 구조만.** 용도·상태를 점으로 잇지 않는다.

**V4 — 다른 층을 가리키는 필드는 가리키는 것의 이름.** `axis` `parameter` `ingredient` `function`
`from`/`to`(IN 만) · `label` · `ko`.

**V5 — 통제 어휘 한 벌.**

| 필드 | 값 | 뜻 |
|---|---|---|
| `direction` | `increase` `decrease` | 원인이 커지면 대상이 커진다 / 작아진다 |
| `magnitude` · `weight` | `weak` `medium` `strong` | 세기 세 단 (엣지 세기 · 역할 무게 · DC 성분). 숫자는 S3 |
| `confidence` | `draft` `low` `medium` `high` | `draft` = 사람이 아직 안 봄 |
| `functional_form` | `linear` `threshold` `saturating` `non_monotonic` | |
| `tier` | `core` `monitored` | 최적화 대상 / 감시만 |
| `goal` | `maintain` `increase` `decrease` `minimize` `maximize` `target` | |
| `method` · `scale_type` | `benchmark_difference` · `diff_7` | 원점 대비 ±3 |
| `evidence_required` | `sample` `sample_aged` | |
| `source` | `{kind: literature\|expert\|prior\|measured\|user, date}` | 옛 `range_source` `source_type` `evidence` |
| `scope` | `any` 또는 `SC[\|APP[\|ST]]` | 없으면 `any` |

**V6 — 스코프는 화살표에만, 파이프 하나, 필드 `scope`.** 사물·카드에는 없다.

**V7 — 집합 꼴 하나.** 재료 엣지 · P.axes · DC 성분 · RP 보상은 전부 `[{axis|ingredient, direction, magnitude, scope?, …}]`
같은 원소 꼴이다. 새 목록을 만들 때 다른 꼴을 짓지 않는다.

---

## 11. 검사

| 규칙 | 검사 |
|---|---|
| V1·V2 | 접두 집합 ⊆ 표, ID 정규식 |
| V5 | 값 ⊆ 표 |
| V6 | `scope` 가 화살표 밖에 없고, 문자열이 트리에 있는 노드로만 됨 |
| §1 | 모든 core 축에 재료→L 직접 엣지가 최소 하나 (P 경유만인 축 = 실체화 대상) |
| §6 | LESSON `observed` 원소마다 대응 엣지가 있다 (없으면 승격 대상) |

## 12. 결정 → `RULES.en.md` (09-17)

이 장의 규칙(§10)과 결정(옛 §12)은 **법전 `RULES.en.md` 가 덮어썼다.** 법전이 정본이고 이 장은 설명이다.
09-13 이후 법전이 이 장과 **다르게** 정한 것:

| 이 장 | 법전 |
|---|---|
| V4 `ko` 필드(문자열 또는 map) | **A8 온톨로지는 영어만.** `label` + `definition`. `ko` 는 레코드에 없고 S4 번역표로 |
| V4 "표시명은 참조에 안 씀" | A7 로 옮김 |
| V5 `source` 표 | A9 그대로 |
| §4 IN 두 목록 | C4 확정 |
| §6 LESSON 관찰 레코드 | C6 확정 |
| §8 카드는 보기 | D1~D4 확정, D6 스냅샷 추가 |
| §9 스코프 대장 불변식 넷 | C9 **다섯** — (v) `(owner, to, scope)` 유일 |
| §0 P 두 갈래(`role`) | 없앰 — 제약은 ING 상·하한과 제형 범위에 (A4) |
