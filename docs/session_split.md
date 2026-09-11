# Session split — 진행도와 세션 분할 (2026-09-11)

한 세션이 온톨로지·모형·앱·API 도구를 다 들고 있어 컨텍스트가 무거워졌다.
이 문서는 **(1) 지금 어디까지 왔는지를 알고리즘 구간 위에 적고, (2) 앞으로 일을
기능별 세션으로 가르는 기준과 각 세션의 계약**을 정한다. 새 세션은 이 문서와
`CLAUDE.md` 를 읽고 시작한다.

기준 알고리즘은 `1st_Draft_algorithm_remi.drawio` (2026-09-04, 저장소 밖 사용자 파일. 구간 이름은
`docs/layer_boundaries.md` 1절).

---

## 1. 진행도 — 알고리즘 구간 위에

| 구간 | 하는 일 | 상태 | 어디에 | 남은 것 |
|---|---|---|---|---|
| `A1` | 사용자 한 문장 | 화면만 | `app/user_flow.py` ① | — |
| `A2-1·2·3` | API 가 문장을 flavor·texture·appearance 로 가르고 벤치마크를 찾는다 | **없음** | — | API 호출 · LEXICON 대조 → 치환/추가 |
| `A3` | 질문 은행에서 되묻는다 | 반쪽 | `app/interview.py` (온톨로지에서 질문 생성) | 어떤 질문을 고를지(B1 SCOPE 정책은 있음) |
| `A4` | Framing — LEXICON·STRUCTURE 의 말로 규정 → **Output 4** | 반쪽 | `user_flow.py` ①②(정체성 축 칩) · `projects/RV_rice_milk/product_card.yaml` | Output 4 YAML 형식 (identity·unresolved) 미작성 |
| `B1-1/2/3` | 벤치마크 분석 / 사용자 설명 / 프로파일링 | 구조만 | AXIS_CARD 9제형 · PRODUCT_CARD 두 층 | B1-1 온라인 분석 없음 |
| `B2` | Target — 카드를 LEXICON 의 말로 치환 → **Output 5** | 반쪽 | `user_flow.py` ② (축 슬라이더 ±3) | Output 5 YAML 형식 |
| `C0` | Process 기록 | 1단계 완료 | `app/process.py` (RM-P1) | PROCESS 레이어(2단계) |
| `C1` | 필수·금지 재료, 제약 | 부분 | 팔레트 `등급`(제한/제외), `filters.py` | 화면 연결 |
| `C2` | 미등록 재료 API 검색·등록 | **없음** | — | API 도구 (fill_typical_api 와 같은 꼴) |
| `C3` | 재료가 충분한가 | 부분 | 도달축 계산 (`add_application.reach_count`, `audit_axis_scope`) | 제품 단위로 |
| `C4` | Gap-fill 설명 | **없음** | — | |
| `C5` | Feasibility → **Output 6** | **없음** | (범위가 오늘 생겨 이제 짤 수 있다) | 목표가 범위 안에서 닿나 |
| `D1` | Build — Γ₀·Λ·Σ₀ 로 이론 배합 → **Output 7** | 완료 | `engine/formulator/mixture.py` · `v2adapter.build/suggest` | 용량-반응 형태(threshold 등) 미반영 |
| `D2` | Record — 관능 결과 | 완료 | `app/dataio.py` (xlsx 규약) | |
| `D3` | Analysis — 벤치마크 0 | 완료 | `app/warmloop.py` | |
| `D4` | Explain · DoE → **Output 8** | v1 잔재 | `doe.py` · `active_design.py` (v1 온톨로지 기준) | v2 연결, 실험 횟수 정책, 척도 표류 |
| `E1` | Record and refit | 부분 | `learn.py` (PLS/GP LOO) | INGREDIENT 환류 없음 |
| `E2` | 최적화 배합 → **Output 9** | 부분 | `optimize.py` (v1 Projection) | v2 연결 |

지식 레이어 쪽 (알고리즘이 읽는 것):

| 레이어 | 상태 |
|---|---|
| LEXICON 216 | 완료. `redefined:` 로 재정의 진행 중 (크리미함·기름짐·윤기·매끄러움 됨) |
| PARAMETER 39 | 완료 (SFC37 신설) |
| INGREDIENT | 엣지 다경로 접힘(수정자 규칙), `limitations`·`dose_response_shape` 있음. 고감미도 감미료 잔존 1행 |
| RELATION 70 | R-1 음료·소스·아이스크림·현탁. 17건 의도된 반대부호 남음 |
| STRUCTURE 9 | 원 4 + 파생 5 (dressing·dip·condiment·soup·beverage_milk) **전부 DRAFT 범위, 사용자 확인 대기** |
| AXIS_CARD 9 파일 | 파생 5개는 형제 복사. jar→diff 통일 |
| PRODUCT_CARD 1 | RV_rice_milk. 제품 팔레트 행 12개 처리 보류 |
| 팔레트 978행 | **오늘** 통상(API) + 범위(하한 0·상한 API upper) 전부. 사람 검토 전 |
| PROCESS | 없음 |

---

## 2. 세션을 가르는 기준

네 가지를 같이 만족하는 선에서 자른다. 하나만 보면 잘못 자른다.

| 기준 | 뜻 | 왜 |
|---|---|---|
| **① 필요한 지식의 종류** | 감각과학 / 재료 과학 / 수학·통계 / 지역 언어·문화 / 소프트웨어 공학 | 한 세션의 시스템 프롬프트·기억이 한 종류 전문가로 좁아져야 답이 깊어진다 |
| **② 쓰기 소유권이 겹치지 않는다** | 한 파일은 한 세션만 고친다. 다른 세션은 읽기만 | 두 세션이 같은 YAML 을 고치면 되돌리기 문제가 생긴다. 이번 세션에서 "다른 세션이 한 일" 확인이 두 번 필요했다 |
| **③ 검증 방법이 다르다** | 시뮬레이션 / 사람 판정표 / selfcheck / 앱 흐름 | 세션의 "끝났다" 기준이 하나여야 한다 |
| **④ 컨텍스트 무게** | 큰 YAML(온톨로지 1.7만 줄)은 한 세션만 싣는다 | 이번 세션이 느려진 원인 |

**자르지 않는 것:** 알고리즘 구간(A/B/C/D/E)으로는 자르지 않는다. 구간은 지식이
섞인다 — `D1` 은 수학이지만 온톨로지를 읽고, `A2` 는 언어학이지만 API 공학이다.
구간은 **세션이 아니라 계약(입출력)**으로 나타난다.

---

## 3. 세션 다섯 — 각 절이 그대로 첫 프롬프트다

각 세션의 블록을 **통째로 복사해서** 새 세션의 첫 메시지로 넣는다. 역할·소유·검증·
첫 일이 한 덩어리라 따로 6절을 두지 않는다. 읽기 권한은 전부 "모두" 다 — 남의
파일을 읽는 것은 자유고, **고치는 것만** 소유표를 따른다.

### S1 `ONTOLOGY` — 감각 언어와 물성 관계

```
remi 저장소 C:\Users\user\OneDrive\Desktop\Remi 1.0\Remi1.0. CLAUDE.md 와
docs/session_split.md 를 먼저 읽어. 이 세션은 S1 ONTOLOGY 다.

역할: Sensory Scientist · Food Scientist
지식: 관능 평가, 관능 언어학(용어 정의 · 앵커 문장 · 척도), 식품 과학
      (물성→관능, 관능↔관능, 물성↔물성 관계)
쓰기 소유: layerL_lexicon.yaml · layerA_parameters.yaml · layerR_seed.yaml ·
      layerS2_profiles.yaml · layerM_cards_*.yaml · docs/척도정의_전략.md ·
      docs/축_의존성_검증전략.md · tools/audit_axis_scope.py ·
      tools/add_application.py · tools/merge_jar_diff.py
읽기: 모두. 위 파일만 고치고 나머지는 읽기만 한다.
검증: python engine/selfcheck_v2.py (44건) · python tools/audit_axis_scope.py (판정 대장)
경계: INGREDIENT 엣지 값이 틀려 보이면 고치지 말고 S2 에 보고한다.

규칙: 설계 결정은 마음대로 진행하지 말고 물어보면서. 시스템의 이름·식별자는 영어,
한글은 화면에 출력되는 문장에만. 도구는 --check 가 기본이고 --write 로만 쓴다.

열린 일: STRUCTURE 파생 5개(dressing·dip·condiment·soup·beverage_milk) DRAFT 범위
확인 · 잎 스코프 정리 · 남은 LEXICON 재정의(대장에서 7/7 된 축은 redefined: 먼저) ·
R-2 반대부호 17건 · spread SC 여부 · 척도 표류 전략(더 배운 뒤 제안) ·
낡은 docs/식감_온톨로지_정리.md 갱신.

첫 일: layerS2_profiles.yaml 의 DRAFT 5개 파라미터 범위를 표로 보여 주고 확인받아.
```

### S2 `INGREDIENT` — 재료 데이터베이스와 범위

```
remi 저장소 C:\Users\user\OneDrive\Desktop\Remi 1.0\Remi1.0. CLAUDE.md 와
docs/session_split.md 를 먼저 읽어. 이 세션은 S2 INGREDIENT 다.

역할: 식품 제품 개발자 · 식품 소재 전문가
지식: 식품 재료 과학(기능군 · 통상 사용량 · 한계 · 대체 · 용량-반응), API 도구 공학
쓰기 소유: ontology_v2/layers/layerC2_*.yaml · data/palette.xlsx ·
      data/typical_review.xlsx · tools/fill_typical_api.py · tools/check_bounds.py ·
      tools/build_palette.py · tools/review_palette.py · tools/apply_palette_review.py ·
      tools/ingredient_axis_map · app/palette.py · docs/bounds_strategy.md
읽기: 모두. 위 파일만 고치고 나머지는 읽기만 한다.
검증: python tools/check_bounds.py (0건 목표) · 검토표의 사람 판정 ·
      data/ingredient_axis_map.xlsx · python engine/selfcheck_v2.py
경계: LEXICON 의 축 정의나 STRUCTURE 스코프가 틀려 보이면 S1 에 보고한다.
API 키: ANTHROPIC_API_KEY 는 사용자 환경변수. 파일·코드에 절대 두지 않는다.

규칙: 설계 결정은 마음대로 진행하지 말고 물어보면서. 시스템의 이름·식별자는 영어,
한글은 화면에 출력되는 문장에만. 도구는 --check 가 기본이고 --write 로만 쓴다.

열린 일: 팔레트 958행 사람 검토 반영 · 잔탄 딥 0.5 판단 · C2 미등록 재료 API
검색·잠정 등록 도구 · C1 등급 화면 연결(S5 와) · 고감미도 감미료 잔존 정리 ·
RV_rice_milk 제품 행 12개(보류 — 실측이 농축 베이스인지부터).

첫 일: data/typical_review_new.xlsx 를 typical_review.xlsx 로 바꾸고, 걸린 행 234건
중 '자릿수' 말고 남은 것부터 판정을 받아.
```

### S3 `MODEL` — 수학적 모형과 실험 설계

```
remi 저장소 C:\Users\user\OneDrive\Desktop\Remi 1.0\Remi1.0. CLAUDE.md 와
docs/session_split.md 를 먼저 읽어. 이 세션은 S3 MODEL 다.

역할: 모델링 과학자
지식: 혼합물 모형 · 베이즈 사전 · 최적화 · 실험계획 · 소표본 통계
쓰기 소유: engine/formulator/* (mixture.py · v2adapter.py · propose.py · structured.py ·
      learn.py · doe.py · active_design.py · optimize.py) · engine/selfcheck_model.py ·
      app/warmloop.py
읽기: 모두 (온톨로지는 V2Ontology 로, 팔레트는 app/palette.load 로). 위 파일만
      고치고 나머지는 읽기만 한다.
검증: python engine/selfcheck_model.py (18건) · python engine/selfcheck_v2.py ·
      시뮬레이션(합성 데이터로 Γ₀ 복원, 가드 발동 확인)
경계: 온톨로지·팔레트 값이 틀려 보여도 고치지 않는다 — S1/S2 에 보고한다.
      척도(RANGE_TO_SD 등)를 바꾸는 결정은 docs/척도정의_전략.md 에 적고 사용자 승인 뒤.

규칙: 설계 결정은 마음대로 진행하지 말고 물어보면서. 시스템의 이름·식별자는 영어,
한글은 화면에 출력되는 문장에만.

열린 일: 용량-반응 형태(linear·threshold·saturating, 팔레트 통상근거에 있음)를 Γ₀ 에
반영할지 · D4 DoE 와 E2 최적화를 v2 로 연결(지금 v1 Projection) · C5 Feasibility(목표가
범위 안에서 닿나) · 실험 횟수 정책 · E1 INGREDIENT 환류 규칙(소급 환류 보류 중) ·
RANGE_TO_SD 재검토는 팔레트 검토 뒤.

첫 일: dose_response 를 Γ₀ 에 어떻게 반영할지 설계안을 내고 물어봐.
```

### S4 `LANGUAGE` — 사용자의 말을 온톨로지의 말로 (지역·언어별)

**S1 과 어디가 겹치고 어디가 다른가.** 둘 다 LEXICON 을 만진다. 그러나

| | S1 ONTOLOGY | S4 LANGUAGE |
|---|---|---|
| 묻는 것 | "크리미함이란 **무엇**인가" — 정의·앵커·척도 | "이 사람이 한 말이 크리미함**인가**" — 대조·치환 |
| 지식 | 감각과학 (보편 — 물리는 나라가 없다) | 언어·문화 (지역 — 같은 물리를 다른 말로 부른다) |
| 쓰기 | LEXICON 정의 | 매핑표 · 질문 은행 · 없는 말 큐. **LEXICON 은 쓰지 않는다** |
| 검증 | selfcheck | 매핑률 · 사람 확인 |

즉 S1 은 **사전**이고 S4 는 **통역**이다. 지금은 한국어 한 지역이라 겹쳐 보이지만,
해외로 가면 갈라진다 — 한국어 "고소하다" 는 영어 한 낱말이 없고, 영어 crispy / crunchy
는 한국어에서 안 갈리고, 일본어 コク 는 셋 다 아니다. 사전(S1)은 그대로 두고 통역(S4)이
지역마다 붙는다. 그래서 S4 의 첫 번째 차원은 **locale** 이다.

**언제 여나.** 지금이 아니다. A2(API 문장 분석) 를 착수할 때 연다. 그 전까지 S4 의 일
가운데 급한 것 — Output 4/5/6 의 YAML 형식 — 은 형식이지 언어가 아니라 S5 가 맡는다.

```
remi 저장소 C:\Users\user\OneDrive\Desktop\Remi 1.0\Remi1.0. CLAUDE.md 와
docs/session_split.md 를 먼저 읽어. 이 세션은 S4 LANGUAGE 다.

역할: 관능 언어 통역자 · 프롬프트 설계자
지식: 지역·언어별 식품 감각 표현(방언·관용·문화), 문장 → flavor·texture·appearance
      삼분류, 어휘 대조·치환, 질문 설계, API 프롬프트·스키마 설계
쓰기 소유: app/intake.py(신설) · app/interview.py · app/user_flow.py ·
      data/lexicon_map_<locale>.xlsx(신설, 말 → L.* 매핑표) · 질문 은행 ·
      data/ko_normalization_review.xlsx
읽기: 모두. 위 파일만 고치고 나머지는 읽기만 한다.
검증: 매핑률(정규화 뒤 93% 기준선) · 사람이 Output 4/5 확인
경계: LEXICON 에 낱말을 직접 더하지 않는다. "없는 말" 목록을 S1 에 넘긴다.
      한 locale 의 표현을 다른 locale 로 옮겨 적지 않는다 — 매핑표는 locale 마다 따로.
API 키: ANTHROPIC_API_KEY 는 사용자 환경변수. 파일·코드에 절대 두지 않는다.

규칙: 설계 결정은 마음대로 진행하지 말고 물어보면서. 시스템의 이름·식별자는 영어,
한글은 화면에 출력되는 문장에만.

열린 일: A2 API 문장 분석 → LEXICON 대조 → 치환/추가 경로(추가는 예외, S1 승인 큐) ·
A3 질문 선택 · B1-1 벤치마크 분석 여부 · locale 확장 설계.

첫 일: 쌀음료 실측 메모와 사용자 문장 샘플로 ko 매핑표 초안을 만들고, 못 붙은 말을
S1 큐로 정리해 보여 줘.
```

### S5 `APP` — 화면·데이터·공정 기록

```
remi 저장소 C:\Users\user\OneDrive\Desktop\Remi 1.0\Remi1.0. CLAUDE.md 와
docs/session_split.md 를 먼저 읽어. 이 세션은 S5 APP 다.

역할: 소프트웨어 엔지니어 · 실험실 운영 흐름 설계자
지식: Streamlit · xlsx · SQLite, 실험실의 실제 작업 순서
쓰기 소유: app/main.py · app/dataio.py · app/store.py · app/process.py ·
      projects/*/ 의 Output 4/5/6 YAML 형식(내용은 S4·사용자, 형식은 S5) ·
      docs/공정_전략.md · README.md · CLAUDE.md · requirements.txt · .gitignore · run.bat
읽기: 모두. 위 파일만 고치고 나머지는 읽기만 한다.
검증: 사용자 흐름 7제품 · 검사 파일 누출(백업·검토 파일이 화면에 뜨지 않는가) ·
      가드(음수 · NaN · |t|>3) · 다섯 검사 전부 초록
경계: 온톨로지·팔레트·모형 코드는 고치지 않는다 — 해당 세션에 보고한다.

규칙: 설계 결정은 마음대로 진행하지 말고 물어보면서. 시스템의 이름·식별자는 영어,
한글은 화면에 출력되는 문장에만.

열린 일: 화면에서 제품(RV_rice_milk)이 제형과 나란히 뜨는 것 정리(제품은 projects/ 것) ·
Output 4(identity·unresolved)/5/6 YAML 형식 확정(제품 폴더에 한 파일씩, 웹 확인,
엑셀은 Output 6만) · Output 6~9 표시 · C1 등급 화면 연결(S2 와) · C0 공정 2단계는 보류.

첫 일: Output 4/5/6 YAML 형식 초안을 projects/RV_rice_milk/ 에 만들어 보여 줘.
```

### 갈라 두지 않는 것

- **PROCESS 레이어**(공정 액추에이터)는 아직 안 만든다. 만들 때 S6 `PROCESS` 로 연다 —
  공정 공학이라 S1~S5 어느 지식도 아니다.
- **색상**은 제외(사용자 결정).

---

## 4. 세션 간 계약

```
S4 LANGUAGE ──매핑·목표──▶ S5 APP ──Output 4/5/6──▶ 사용자
   │ "없는 말"                  │ 실측 xlsx
   ▼                           ▼
S1 ONTOLOGY ──YAML──▶ S3 MODEL ◀──팔레트(통상·범위)── S2 INGREDIENT
   ▲                    │ Γ₀ 복원·가드 결과·틀려 보이는 값 보고
   └────────────────────┘
```

규칙 넷:

1. **한 파일 한 주인.** 3절 소유표에 없는 파일을 고쳐야 하면 그 세션 주인에게 넘긴다.
   급하면 고치되 커밋 메시지 첫 줄에 `[S2→S1]` 처럼 적는다.
2. **공통 검사는 어느 세션이든 돌린다.** `selfcheck_v2` · `selfcheck_model` · `check_bounds --check`.
   빨간불이 남의 영역이면 고치지 말고 보고한다.
3. **결정은 문서로.** 세션 밖으로 나가는 결정(척도·범위 규칙·레이어 경계)은 `docs/` 에
   적고 커밋한다. 채팅에만 있는 결정은 다른 세션이 못 본다. `CLAUDE.md` 는 S5 가 관리하되
   "지키기로 한 것" 표는 누구든 덧붙인다.
4. **푸시는 세션이 끝날 때.** 시작할 때 `git pull` 먼저.

---

## 5. 지금 열린 것 (세션별 배정)

| 항목 | 세션 |
|---|---|
| `typical_review_new.xlsx` → `typical_review.xlsx` 교체(파일 잠김) | S2 |
| 팔레트 958행 사람 검토 · 잔탄 딥 0.5 | S2 |
| STRUCTURE 파생 5개 DRAFT 범위 확인 | S1 |
| RV_rice_milk 제품 행 12 (실측이 농축 베이스인지) | 보류 — S2 |
| Output 4/5/6 YAML 형식 | S5 |
| 용량-반응 형태 반영 · DoE/최적화 v2 연결 · C5 | S3 |
| 척도 표류 전략 · spread SC · R-2 17건 · LEXICON 재정의 · 낡은 문서 | S1 |
| C2 재료 검색·등록 도구 | S2 |
| 화면의 제품/제형 분리 · Output 표시 | S5 |
| A2 API 문장 분석 · ko 매핑표 · locale | S4 (A2 착수 시 연다) |
| PROCESS 2단계 · 소급 환류 · 색상 | 보류 |
