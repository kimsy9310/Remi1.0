# 02 명사구 — 제품 = 구조 × 용도 (× 상태) + 재료 + 정체성 축. 용도는 제품·재료를 담지 않는다

4차 2026-09-13 (S1). 트리는 평평하게(계층 보류) · 파일 이름 · 짧은 키 · `private` 라벨 · 제품 카드 한 장 · 동일성 세 관점. 규칙은 `RULES.md` B 절. 규칙은 제안이고 사용자 확인 뒤 확정.

이 장이 정하는 것: "무엇을 만드는가" 를 적는 법. 제형(STRUCTURE 프로파일)과 제품
(projects/)의 경계, 각각을 부르는 **단 하나의 이름**, 정체성 축의 자리. 개별 ID 표기는
01장, Output 4 의 필드 전체는 05장.

---

## 현황 — 재 봄 (2026-09-12)

### 제형 하나를 부르는 이름이 일곱

음료 제형(`SC.emulsion.ow` 위의 `APP.beverage`)을 예로:

| # | 어디 | 무엇 | 값 |
|---|---|---|---|
| 1 | 정본 로더 `PROFILES` 키 · `product_card.meta.structure` · `frame.structure.profile` · 카드 파일명 | 짧은 키 | `beverage` |
| 2 | STRUCTURE `structure_class` + `application` + `state` | 정체성 세 축 | `SC.emulsion.ow` · `APP.beverage` · `null` |
| 3 | STRUCTURE `label` · AXIS_CARD `meta.profile` · **`derived_from`(참조로 씀)** | 영어 표시명 | `Oil-in-water emulsion beverage` |
| 4 | STRUCTURE `ko.label` | 한국어 표시명 | `수중유 에멀전 음료` |
| 5 | RELATION `scope` · AXIS_CARD `active_in` | 스코프 (파이프) | `SC.emulsion.ow\|APP.beverage` |
| 6 | INGREDIENT `scoped_to_structure_class` | 스코프 (점) | `SC.emulsion.ow.beverage` |
| 7 | STRUCTURE `source_file` · 데이터 파일명 | v0 파일 이름 | `ow_emulsion_beverage_layerA.yaml` · `beverage_warmloop_260720.xlsx` |

짧은 키(1) 일곱 개도 규칙이 없다 — `beverage` `dressing` `dip` `condiment` 는 용도
이름, `sauce_ow` 는 용도+구조, `suspension` 은 구조, **`icecream` 은 제품 이름**이다
(정체성은 `SC.emulsion.ow|APP.dessert|ST.frozen`).

### 제품과 제형이 섞였던 자리 (이력)

    beverage_coffee_milk · beverage_rice_milk    제품이 프로파일 등록부에 (09-10 뺌)
    APP.beverage.milk                            재료가 용도 이름에 (09-12 뺌)
    현탁액 meta 의 "default product"             제품이 제형 파일에 (09-10 뺌)
    icecream                                     제품 이름이 프로파일 키에 (남아 있음)

넷 다 같은 실수다 — **제품에 속한 정보를 제형의 이름에 넣었다.**

### 제품 쪽 이름

| 어디 | 필드 | 값 |
|---|---|---|
| 폴더 | `projects/<id>/` | `RV_rice_milk` |
| product_card | `meta.id` · `meta.ko` · `meta.kind: product` · `meta.structure` | `RV_rice_milk` · `쌀 음료` · `beverage` |
| frame (Output 4, S5 초안) | `meta.product` · `structure.{profile, sc, app}` · `identity[].term` | 같은 것을 셋으로 |

---

## 제품을 정하는 프로파일은 넷 — 제형은 그중 하나다

사용자 피드백 (09-12): *"ST 는 사실상 frozen 뿐이라 제형은 SC 와 APP 로 갈린다. 제형은 제품을
정의하는 한 유형이지 주 지표가 아니다. `SC.emulsion.ow|APP.beverage` + `ING.soy_milk` 와
`+ ING.milk` 는 다른 제품인데 비슷해 보인다 — 확실히 구분해야 한다."*

재 보면 맞다. ST 는 `frozen` 24건뿐이고, 제형 7개는 SC 2 × APP 6 조합이다. 제형은 **물리 틀**
이지 제품이 아니다 — 같은 틀에 두유·우유·쌀음료가 다 들어간다. 제품을 정하는 것은 넷이다:

| 프로파일 | 답하는 질문 | 어휘 | 어디 | 두유 vs 우유에서 |
|---|---|---|---|---|
| 구조 프로파일 (제형) | 어떤 물리 틀인가 | `SC` `APP` `ST` | STRUCTURE | **같다** — 둘 다 `SC.emulsion.ow\|APP.beverage` |
| 재료 프로파일 | 무엇으로 만드나 — **핵심 재료** | `ING` `FT` | `projects/<id>/` (Output 4 `seed_ingredients` · Output 6 팔레트) | **다르다** — `ING.soy_milk` vs `ING.milk` |
| 감각 프로파일 | 무엇이 이 제품답게 하나 — 정체성 축과 목표 | `L` + goal ±3 | PRODUCT_CARD · Output 4 `identity` · Output 5 | **다르다** — `L.ar.beany` vs `L.ar.creamy_dairy_aroma` |
| 원점 프로파일 | 무엇과 비교하나 — 기준 제품·첫 시제품 | 제품 id · sample_id | Output 5 `origin` | 다르다 |

(공정 프로파일은 PROCESS 가 생기면 다섯째.)

**"제품 동일성" 의 뜻 (09-13 질문 — 보는 사람마다 다르다).** 세 관점이 정말 다르고, 문법이
정하는 것은 셋째다:

| 관점 | "같은 제품" 이란 | 무엇이 걸리나 |
|---|---|---|
| 사용자 | 내 프로젝트. 배합을 바꿔도 같은 제품(버전이 는다) | 제품 id 하나 · `private` 라벨 |
| 전문가 · 시장 | 같은 부류 — 두유와 우유는 다른 제품, 두 회사 두유는 같은 부류 | 제형 + 핵심 재료 |
| **모형 (AI)** | **점수를 같은 자에 놓고 비교해도 되는 시료들** | 제형 + 핵심 재료 + 원점 |

모형의 관점이 문법에 들어가는 이유: ±3 점수는 원점(기준 제품) 대비이고, 좌표는 제품마다 격리된다
(09-10 결정 "좌표는 격리하고 기울기는 공유"). 핵심 재료가 다르면 같은 "크리미함 +1" 이 다른 물리라
같은 자에 놓을 수 없고, 원점이 다르면 0 의 뜻이 다르다. 그래서:

**규칙 — 제품의 동일성 (모형 관점).** 두 시료가 같은 제품이려면 제형 · 핵심 재료 · 원점이 같아야
한다. 정체성 축이 바뀌면 같은 제품의 **새 버전**(원점을 새로 잡는다). 제형만 같은 것은
**형제**다. 형제는 제형의 축 카드·파라미터 범위·제형 스코프 엣지를 공유하고, 재료·정체성 축·
원점은 공유하지 않는다. 비슷해 보이는 이유는 첫 프로파일만 보기 때문이고, 구분하는 법은
**둘째와 셋째를 반드시 적는 것**이다 — Output 4 에서 `seed_ingredients` 와 `identity` 가 비어
있으면 제품이 정의되지 않은 것이다 (05장이 필수로 못 박는다).

**핵심 재료란.** 팔레트 전체가 아니라 **없으면 그 제품이 아닌 재료** — 두유의 콩, 쌀음료의 쌀,
아이스크림의 유지. 재료 프로파일은 `key_ingredients: [ING.*]` 한 줄이고 나머지 팔레트는 C1~C3
의 일이다. 핵심 재료가 정체성 축을 데려온다(재료의존 축: 콩 → 콩 비린내, 쌀 → 밥 향).

---

## 계층 전략 — SC · APP · ST 를 트리로 세운다

사용자 피드백 (09-12): *"제품을 정의하는 이름공간은 계층을 적용해 온톨로지로 만들어야
한다. 지속적으로 오류가 난다."* 되짚어 보니 오류 다섯이 **전부 한 가지 결핍**에서 왔다 —
세 축에 트리가 없고, 제형이 받는 스코프를 **손으로 적어** 왔다.

| 오류 (이력) | 트리가 있었다면 |
|---|---|
| `SC.frozen.ice_cream` — 구조·용도·상태를 한 SC 처럼 적음 | SC 트리에 없는 이름이라 검사에 걸린다 |
| `APP.beverage.milk` — 재료를 용도 이름에 넣음 | APP 트리에 `milk` 노드를 세우려면 "어떻게 먹나" 로 답해야 하는데 답이 없다 |
| `beverage_coffee_milk` — 제품을 제형 등록부에 올림 | 등록부가 세 축의 조합으로만 생성되므로 들어갈 자리가 없다 |
| `dose_parent` (add_application) — 드레싱이 소스의 엣지를 받게 하려고 임시 필드를 만듦 | APP 트리에서 `dressing` 이 `sauce` 의 자식이면 상속으로 끝난다 |
| 아이스크림 `scopes` 에 `SC.emulsion.ow` 가 빠져 형제로 인식 안 됨 (09-10) | 스코프 집합이 트리에서 **계산**되므로 빠질 수 없다 |

### 세 트리 — 지금 쓰는 노드만 (09-13 결정)

노드를 세우는 데 신중하기로 했다. **예약 노드는 두지 않고, 부모-자식(dressing ⊂ sauce)도 보류**한다 —
마요네즈처럼 소스이자 딥인 것이 있어 `APP.sauce` 의 폭을 먼저 정해야 한다. 지금 트리는 평평하다:

    SC   emulsion.ow · suspension                                   (2)
    APP  beverage · sauce · dressing · dip · condiment · dessert    (6)
    ST   frozen                                                     (1 — 없으면 상온)

계층은 규칙(RULES B4)이 확정된 뒤 노드마다 따로 논의한다. 트리가 평평한 동안 B5·B6(덮기·상속)은
"같으면 덮는다" 로 줄어든다 — 그래도 `any` 와 `SC` 만 적은 스코프가 하위 조합을 덮는 것은 그대로다.

### 조합 규칙

    제형(profile)  = SC 잎  ×  APP 노드(또는 없음)  ×  ST(없으면 ambient)
    스코프(scope)  = 같은 꼴의 문자열인데 각 단이 트리의 **조상**이어도 된다
    덮는다         스코프 s 가 제형 p 를 덮는다  ⇔  s 의 적힌 단마다 p 의 그 단의 조상이거나 같다
                   any 는 전부를 덮는다
    받는 스코프    제형 p 가 받는 스코프 집합 = p 를 덮는 모든 s  — 손으로 적지 않고 계산한다
    이긴다         한 관계가 여러 단에 있으면 p 에 **더 가까운** 단이 이긴다 (잎이 이긴다)

예: `SC.emulsion.ow|APP.sauce.dressing` 이 받는 스코프 =
`any` · `SC.emulsion` · `SC.emulsion.ow` · `SC.emulsion.ow|APP.sauce` · `SC.emulsion.ow|APP.sauce.dressing`.
정본 로더가 지금 손으로 적은 `scopes={'any','SC.emulsion.ow','SC.emulsion.ow.sauce', …}` 과
같은 집합이 되고, `dose_parent` 는 필요 없어진다.

### 점 표기 별칭 — 1.1 이관 때 한 번에

| 옛 (INGREDIENT 125건) | 새 |
|---|---|
| `SC.emulsion.ow.beverage` | `SC.emulsion.ow\|APP.beverage` |
| `SC.emulsion.ow.sauce` | `SC.emulsion.ow\|APP.sauce` |
| `SC.frozen.ice_cream` | `SC.emulsion.ow\|APP.dessert\|ST.frozen` |

### 어디에 두나 — 파일 이름 (09-13 질문 "layerS 는 어디서 나왔나")

`layerS` 는 새 이름이 아니라 **옛 글자 관습**이다. 지금 파일들이 `layer<글자>_<이름>.yaml` 꼴이다 —
`layerL_lexicon` `layerA_parameters` `layerC2_*` `layerR_seed` `layerS2_profiles` `layerM_cards_*`.
글자는 v1 레이어 글자(L·A·C·R·S·M)이고 `S2` `C2` 의 2 는 "스펙 v2 판" 이라는 뜻이다(2026-08-18
이관 머리글). `layerS1` 같은 파일은 없다. 내가 `layerS_taxonomy` 라 쓴 것은 "STRUCTURE 층(S)의
파일" 이라는 뜻이었는데, 09-10 에 레이어 이름을 글자에서 낱말로 바꿨으니 **새 파일은 낱말로**
짓는 것이 맞다:

    ontology_v2/layers/structure_taxonomy.yaml      세 트리 + 점 표기 별칭 표   (S1, 신설)

`layerS2_profiles.yaml` 은 조합(제형)만 들고, 정본 로더의 `PROFILES[*].scopes` 는 taxonomy 에서
계산한다(구현 1.1). 옛 `layer<글자>` 파일명도 1.1 이관 때 낱말로 바꾼다(`structure_profiles.yaml`
등, RULES E2). 그때까지는 이 문서가 정본이고 로더의 손 목록은 이 문서와 같아야 한다.

---

## 규칙 (제안)

**P1 — 두 층, 네 낱말.** 이 네 낱말만 쓴다.

| 낱말 | 뜻 | 어디 사나 | ID |
|---|---|---|---|
| `structure` | 구조 부류. 물리가 가른다 | STRUCTURE | `SC.*` |
| `application` | 용도. 사용자가 말한 명사에서 온다 | STRUCTURE | `APP.*` |
| `state` | 상태. 먹는 순간의 상 | STRUCTURE | `ST.*` |
| `profile` | 위 셋의 한 조합 = **제형**. 파라미터 범위·축 카드·필러를 가진다 | STRUCTURE 항목 하나 · AXIS_CARD 파일 하나 | 스코프 문자열 |
| `product` | 제형 + 재료 + 정체성 축 + 기준 제품 | `projects/<id>/` | 제품 id |

"제형" 은 profile 의 한국어, "제품" 은 product 의 한국어다. `structure` 를 profile 의 뜻으로
쓰지 않는다 (`product_card.meta.structure: beverage` 는 옛 이름 → `profile`).

**P2 — 용도는 제품·재료를 담지 않는다.** `APP.*` 이름에 재료·브랜드·제품 명사가 들어
가면 틀린 것이다. 재료가 가르는 것은 재료가 가른다:

    유음료     = SC.emulsion.ow|APP.beverage  +  ING.milk
    쌀음료     = SC.emulsion.ow|APP.beverage  +  ING.rice_*
    아이스크림 = SC.emulsion.ow|APP.dessert|ST.frozen   (제품명 아님 — 제형이다)

같은 이유로 제형 파일에는 **제품 고유 축(향·매운맛)이 없다** (09-02 결정). 축이 제품에
있는 이유는 다섯뿐이며 "제품의존" 은 없다 — 보편 · 제형의존 · 재료의존 · 공정의존 ·
엣지결손 (`CLAUDE.md`).

**P3 — 제형의 정본 이름은 스코프 문자열이다.** `SC.emulsion.ow|APP.beverage`. 짧은 키는
그 별칭이고 다음 규칙으로 **만들어진다** (손으로 짓지 않는다).

**짧은 키가 무엇인가 (09-13 질문).** 스코프 문자열은 길고 `|` 가 들어 파일명·URL·xlsx 열·함수
인자에 못 쓴다. 그래서 짧은 별명이 필요하고, 지금 다섯 곳이 그것을 쓴다: 정본 로더 `PROFILES` 의
키 · 제품 카드 `profile:` · 앱의 제형 선택값 · 데이터 파일 접두(`beverage_warmloop_…`) · (없어질)
카드 파일명. 문제는 지금 키 일곱이 **손으로 지어져** 규칙이 없다는 것 — `sauce_ow` 는 구조를 붙였고
`icecream` 은 제품 이름이다. 손으로 지으면 같은 제형에 두 이름이 생기거나(오늘 `beverage_cloud`)
제품 이름이 들어온다. 규칙으로 만들면 **제형이 정해지는 순간 키도 정해진다**:

    1  APP 이 있으면   키 = APP 의 마지막 마디            SC.emulsion.ow|APP.beverage   → beverage
    2  APP 이 없으면   키 = SC 의 마지막 마디             SC.suspension                 → suspension
    3  ST 가 상온이 아니면  뒤에 _<ST 마지막 마디>       SC.emulsion.ow|APP.dessert|ST.frozen → dessert_frozen
    4  같은 APP 이 두 SC 에 있으면  앞에 <SC 마지막 마디>_   (아직 없음: 소스가 현탁액에도 생기면 suspension_sauce · ow_sauce)

지금 키와의 대조:

| 제형 | 지금 키 | 규칙 키 | 바뀌나 |
|---|---|---|---|
| `SC.emulsion.ow\|APP.beverage` | `beverage` | `beverage` | — |
| `SC.emulsion.ow\|APP.sauce` | `sauce_ow` | `sauce` | **바뀜** |
| `SC.emulsion.ow\|APP.dressing` · `\|APP.dip` | `dressing` · `dip` | 같음 | — |
| `SC.suspension` | `suspension` | `suspension` | — |
| `SC.suspension\|APP.condiment` | `condiment` | `condiment` | — |
| `SC.emulsion.ow\|APP.dessert\|ST.frozen` | `icecream` | `dessert_frozen` | **바뀜** |

키는 별명일 뿐 정본이 아니다 — 트리를 바꾸면(예: dressing 이 sauce 밑으로) 키는 규칙대로 다시
만들어지고, 옛 키는 별칭 표에 남는다. 두 건의 개명은 데이터 파일 · 앱 코드가 걸려 1.1 이관표 #7.

`label` · `ko.label` 은 표시용이며 **참조에 쓰지 않는다** (`derived_from: Oil-in-water
emulsion sauce` 는 반례 → `derived_from: sauce`).

**P4 — 제품의 정본 이름은 `projects/<id>/` 의 id 하나.** 영어 snake, `ko` 는 표시용.
제품은 제형을 짧은 키로 가리킨다 (`profile: beverage`). SC·APP·ST 를 따로 다시 적지
않는다 — 키에서 풀린다. 단, **A2~A4 사이(아직 확정 전)** 에는 셋이 따로 채워질 수 있으
므로 Output 4 는 셋을 받고 확정 때 키로 접는다 (05장).

**P4-1 — 사용자 고유 라벨은 `private` 절에 (09-13).** `RV_rice_milk` 의 `RV` 는 사용자가 붙인
프로젝트 이름이었다. 그런 것 — 프로젝트명 · 고객 · 사내 코드 · 담당자 — 은 **그 사용자만 아는 것**
이고 학습·공유 대상이 아니다. 제품 카드에 자리를 따로 둔다:

    meta:
      id: rice_milk_01              # 시스템이 만드는 영어 키. 뜻이 없어도 된다
      ko: 쌀 음료                    # 화면 표시
    private:                        # 이 사용자만. 온톨로지 · 학습 · 다른 사용자에게 절대 나가지 않는다
      project: RV
      customer: …
      code: …

`private` 아래는 도구가 읽지 않고(엣지 환류 · 공유 온톨로지 · API 프롬프트 어디에도 넣지 않음),
저장은 사용자 폴더(`projects/`)에만 한다 — 알고리즘 그림의 "클라우드 개별 보안 폴더" 가 이 자리다.

**P4-2 — 제품 카드는 AI 가 제품을 이해하는 한 장 (09-13 의견).** 사용자 제안: *"프로젝트명을 설명할
때 AI 는 제형 · 핵심 재료 · 향미 프로파일이 적힌 카드가 있어야 편하지 않나."* 맞고, 그것이 바로
**프로파일 넷을 한 장에 적은 것**이다. 지금은 그 정보가 두 파일로 갈라져 있다 — S5 초안
`frame.yaml`(Output 4: 제형 · 정체성 축 · 씨앗 재료 · 기준 제품 · 못 붙인 말)과
`product_card.yaml`(축 덮어쓰기 · 실측 열). 내 의견은 **한 장으로 합친다**:

    product_card.yaml
      meta        id · ko · 상태 · 날짜
      private     사용자 고유 라벨 (P4-1)
      profiles    구조(profile 키) · key_ingredients · identity(정체성 축 + goal) · origin(기준 제품)   ← 프로파일 넷 = Output 4 의 내용
      axes        제형 카드에서 벗어나는 것 (tier · goal · drop · legacy_column · 제품 주의)
      unresolved  렉시콘에 못 붙인 말 (S4 → S1 큐)

Output 4 는 이 카드의 `profiles` 절이 사용자 확인을 받은 순간의 상태다 — 별도 파일이 아니라
**같은 카드의 확정 표시**(`meta.status: confirmed`). 형식은 S5 몫이라 여기서는 내용만 정한다.
AI 가 프로젝트명을 받으면 이 한 장을 읽고 "쌀음료(O/W 음료 · 쌀 · 밥 향과 크리미함이 정체성 ·
기준은 현재 생산품)" 이라 말할 수 있어야 한다. 그것이 카드가 통과해야 할 시험이다.

**P5 — 정체성 축은 제품의 것, 2~3개, `L.*` 만.** 제형 카드의 tier 와 다른 층이다 —
"무엇을 앞세울지" 이지 "존재하는지" 가 아니다. 필드 이름은 `identity` 안의 `axis`
(01장 V4; S5 초안의 `term` 은 옛 이름).

**P6 — 파생 제형은 부모를 키로 가리키고 `confidence: draft` 로 태어난다.** 검토 전까지
값은 부모의 것이다. 검토가 끝나면 `status: reviewed <날짜>` 와 근거를 남긴다 (09-12 의
dressing · dip · condiment 가 예).

---

## 예 · 반례

    profile: beverage                                  예
    SC.emulsion.ow|APP.beverage + ING.milk             예 — 유음료
    APP.beverage.milk                                  반례 — P2
    icecream (프로파일 키)                              반례 — P3, 제품명. dessert_frozen
    sauce_ow (프로파일 키)                              반례 — P3, 손으로 지은 키. sauce
    derived_from: Oil-in-water emulsion sauce          반례 — P3, 표시명으로 참조
    meta.structure: beverage                           반례 — P1, structure 는 SC 의 자리
    beverage_rice_milk (프로파일)                       반례 — P2, 제품이 제형 자리에

---

## 검사

| 규칙 | 검사 | 상태 |
|---|---|---|
| P2 | `APP.*` 이름의 마지막 마디가 `ING.*` 나 제품 id 와 겹치지 않는가 | 없음 — 만들 것 |
| P3 | 로더 `PROFILES` 키가 규칙으로 만든 키와 같은가 | 없음 — 지금은 `sauce_ow` `icecream` 두 건 어긋남 (1.1 이관) |
| P3 | `derived_from` 이 프로파일 키인가 | 없음 — 지금 3건 표시명 |
| P5 | product_card / frame 의 identity 가 2~3개이고 전부 `L.*` 인가 | 없음 — 만들 것 |

---

## 판단 → `RULES.en.md` B 절 (09-17 전부 확정)

법전이 이 장과 **다르게** 정한 것:

| 이 장 | 법전 |
|---|---|
| ST 는 `frozen` 하나, 없으면 상온 | **B0/B4 ST 네 값** `frozen` `chilled` `ambient` `hot`; 제형은 세 칸을 **모두 적는다**(B5). `ST.ambient` 를 생략하지 않는다 |
| 조합 규칙 "조상이어도 된다" | 트리가 평평하므로 B5 는 "적힌 칸이 같다" 만. 하위 단계는 보류 #1 |
| 이름이 안 맞는 형제 | **B5-1 특성으로 대신 맞추기** — `discriminators` 범위 겹침이 가장 큰 같은 SC 제형에서 빌림, 확신도 −1 |
| 분산상이 여럿인 제품 | **B14** 식감을 지배하는 상이 SC; SC 하나, 무게 없음 |
| P4-1 `private` | B12 확정 |
| P4-2 제품 카드 한 장 | B10 확정 (형식은 S5) |
| 동일성 세 관점 | B9 확정 + **B16 변형**(설탕 없는 같은 제품 = 새 버전, 핵심 재료 빠지면 형제) |
| 저장·가시성 | **B15 저장 세 층**(공유 온톨로지는 기밀) · **E4 가시성 세 등급** · E5 관련 노드 경계(초안) |
| 시험 사례 | 슬러시 · 셔벗 · 마시는 요구르트는 새 값 없이 됨; 떠먹는 요구르트만 `SC.gel` 필요 (보류 #1) |
