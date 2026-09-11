# Session split — 진행도와 세션 분할 (2026-09-11)

한 세션이 온톨로지·모형·앱·API 도구를 다 들고 있어 컨텍스트가 무거워졌다.
이 문서는 **(1) 지금 어디까지 왔는지를 알고리즘 구간 위에 적고, (2) 앞으로 일을
기능별 세션으로 가르는 기준과 각 세션의 계약**을 정한다. 새 세션은 이 문서와
`CLAUDE.md` 를 읽고 시작한다.

기준 알고리즘은 `Algorithm_Remi/1st_Draft_algorithm_remi.drawio` (구간 이름은
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
| **① 필요한 지식의 종류** | 수학·통계 / 감각 언어학 / 식품 재료 과학 / 소프트웨어 공학 | 한 세션의 시스템 프롬프트·기억이 한 종류 전문가로 좁아져야 답이 깊어진다 |
| **② 쓰기 소유권이 겹치지 않는다** | 한 파일은 한 세션만 고친다. 다른 세션은 읽기만 | 두 세션이 같은 YAML 을 고치면 되돌리기 문제가 생긴다. 이번 세션에서 "다른 세션이 한 일" 확인이 두 번 필요했다 |
| **③ 검증 방법이 다르다** | 시뮬레이션 / 사람 판정표 / selfcheck / 앱 흐름 | 세션의 "끝났다" 기준이 하나여야 한다 |
| **④ 컨텍스트 무게** | 큰 YAML(온톨로지 1.7만 줄)은 한 세션만 싣는다 | 이번 세션이 느려진 원인 |

**자르지 않는 것:** 알고리즘 구간(A/B/C/D/E)으로는 자르지 않는다. 구간은 지식이
섞인다 — `D1` 은 수학이지만 온톨로지를 읽고, `A2` 는 언어학이지만 API 공학이다.
구간은 **세션이 아니라 계약(입출력)**으로 나타난다.

---

## 3. 세션 다섯

### S1 `ONTOLOGY` — 감각 언어와 물성 관계

- **지식**: 감각과학·관능 언어학(용어 정의·앵커 문장·척도), 식품 물리(물성→감각).
- **쓰기 소유**: `layerL_lexicon.yaml` · `layerA_parameters.yaml` · `layerR_seed.yaml` ·
  `layerS2_profiles.yaml` · `layerM_cards_*.yaml` · `docs/척도정의_전략.md` ·
  `docs/축_의존성_검증전략.md` · `tools/audit_axis_scope.py` · `tools/add_application.py` ·
  `tools/merge_jar_diff.py`.
- **읽기만**: INGREDIENT (엣지가 어느 축에 닿는지 볼 때).
- **검증**: `engine/selfcheck_v2.py` 44건 · `audit_axis_scope` 판정 대장.
- **당장 할 일**: STRUCTURE 파생 5개 범위 확인받기 · 잎 스코프 정리 · 남은 LEXICON 재정의
  (대장에서 7/7 된 축은 `redefined:` 먼저) · R-2 17건 · spread SC 여부 · 척도 표류 전략(더
  배운 뒤 제안) · 낡은 `docs/식감_온톨로지_정리.md` 갱신.

### S2 `INGREDIENT` — 재료 데이터베이스와 범위

- **지식**: 식품 재료 과학(기능군·통상 사용량·한계·대체), API 도구 공학.
- **쓰기 소유**: `layerC2_*.yaml` · `data/palette.xlsx` · `data/typical_review.xlsx` ·
  `tools/fill_typical_api.py` · `tools/check_bounds.py` · `tools/build_palette.py` ·
  `tools/review_palette.py` · `tools/apply_palette_review.py` · `tools/ingredient_axis_map` ·
  `app/palette.py` · `docs/bounds_strategy.md`.
- **읽기만**: LEXICON(축 이름) · STRUCTURE(제형 스코프).
- **검증**: `check_bounds --check` 0건 목표 · 검토표의 사람 판정 · `ingredient_axis_map.xlsx`.
- **당장 할 일**: `typical_review.xlsx` 958행 사람 검토 반영 · 잔탄 딥 0.5 판단 · `C2` 미등록
  재료 API 검색·잠정 등록 도구 · `C1` 등급 화면 연결 · 고감미도 감미료 잔존 정리 ·
  RV_rice_milk 제품 행 12개(보류).
- **API 키**: `ANTHROPIC_API_KEY` 사용자 환경변수. 파일·코드에 절대 안 둔다.

### S3 `MODEL` — 수학적 모형과 실험 설계

- **지식**: 혼합물 모형·베이즈 사전·최적화·실험계획·소표본 통계.
- **쓰기 소유**: `engine/formulator/*` (`mixture.py` · `v2adapter.py` · `propose.py` ·
  `structured.py` · `learn.py` · `doe.py` · `active_design.py` · `optimize.py`) ·
  `engine/selfcheck_model.py` · `app/warmloop.py`.
- **읽기만**: 온톨로지 전부(`V2Ontology` 로), 팔레트(`app/palette.load`).
- **검증**: `selfcheck_model.py` 18건 · 시뮬레이션(합성 데이터로 Γ₀ 복원, 가드 발동).
- **당장 할 일**: 용량-반응 형태(`threshold`·`saturating`, 통상근거에 있음) 를 Γ₀ 에 반영할지
  설계 · `D4` DoE·`E2` 최적화를 v2 로 연결(지금 v1 `Projection`) · `C5` Feasibility(범위 안에서
  목표가 닿나) · 실험 횟수 정책 · `E1` INGREDIENT 환류 규칙(소급 환류 보류 중) ·
  `RANGE_TO_SD` 재검토는 팔레트 검토 뒤.
- **경계**: 온톨로지 값이 틀려 보여도 고치지 않는다 — S1/S2 에 보고한다.

### S4 `INTAKE` — 사용자 말을 온톨로지 말로

- **지식**: 언어학(문장 → 감각 삼분류 → 어휘 대조·치환), 프롬프트·스키마 설계, 질문 설계.
- **쓰기 소유**: `app/interview.py` · `app/user_flow.py` · (신설) `app/intake.py` ·
  `projects/*/product_card.yaml` · Output 4/5/6 YAML 형식 문서 · 질문 은행.
- **읽기만**: LEXICON(대조 대상) · STRUCTURE · AXIS_CARD.
- **검증**: 매핑률(정규화 뒤 93% 기준) · 사람이 Output 4/5 확인.
- **당장 할 일**: `A2` API 문장 분석 → LEXICON 대조 → 치환/추가 경로(추가는 예외, S1 승인
  큐로) · Output 4(identity·unresolved)/5/6 YAML 형식 확정(제품 폴더에 한 파일씩, 웹 확인,
  엑셀은 Output 6만) · `A3` 질문 선택 · `B1-1` 벤치마크 분석 여부 · `ko_normalization_review.xlsx`.
- **경계**: LEXICON 에 낱말을 직접 추가하지 않는다. "없는 말" 목록을 S1 에 넘긴다.

### S5 `APP` — 화면·데이터·공정 기록

- **지식**: 소프트웨어 공학(Streamlit·xlsx·SQLite), 실험실 운영 흐름.
- **쓰기 소유**: `app/main.py` · `app/dataio.py` · `app/store.py` · `app/process.py` ·
  `docs/공정_전략.md` · `requirements.txt` · `.gitignore` · `CLAUDE.md` 상태표.
- **읽기만**: 나머지 전부.
- **검증**: 사용자 흐름 7제품 · 검사 파일 누출(백업·검토 파일) · 가드(음수·NaN·|t|>3).
- **당장 할 일**: 화면에서 제품이 제형과 나란히 뜨는 것 정리(제품은 `projects/` 것) ·
  `C0` 공정 2단계(PROCESS 레이어)는 보류 · Output 6~9 표시 · 원격 푸시 정리.

### 갈라 두지 않는 것

- **PROCESS 레이어**(공정 액추에이터)는 아직 안 만든다. 만들 때 S6 `PROCESS` 로 연다 —
  공정 공학이라 S1~S5 어느 지식도 아니다.
- **색상**은 제외(사용자 결정).

---

## 4. 세션 간 계약

```
S4 INTAKE ──Output 4/5 (product_card, 목표)──▶ S5 APP ──▶ 사용자
   │ "없는 말"                                     │ 실측 xlsx
   ▼                                              ▼
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
| 미푸시 7건 (`c09b708`…`4f852a2`) | S5 (또는 사용자) |
| `typical_review_new.xlsx` → `typical_review.xlsx` 교체(파일 잠김) | S2 |
| 팔레트 958행 사람 검토 · 잔탄 딥 0.5 | S2 |
| STRUCTURE 파생 5개 DRAFT 범위 확인 | S1 |
| RV_rice_milk 제품 행 12 (실측이 농축 베이스인지) | 보류 — S2 |
| Output 4/5/6 YAML 형식 | S4 |
| 용량-반응 형태 반영 · DoE/최적화 v2 연결 · C5 | S3 |
| 척도 표류 전략 · spread SC · R-2 17건 · LEXICON 재정의 · 낡은 문서 | S1 |
| C2 재료 검색·등록 도구 | S2 |
| 화면의 제품/제형 분리 · Output 표시 | S5 |
| PROCESS 2단계 · 소급 환류 · 색상 | 보류 |

---

## 6. 각 세션의 첫 프롬프트 (복사해서 쓴다)

공통 머리:

> remi 저장소 `C:\Users\user\OneDrive\Desktop\Remi 1.0\Remi1.0`. `CLAUDE.md` 와
> `docs/session_split.md` 를 먼저 읽어. 이 세션은 **S_ `____`** 다 — 3절의 쓰기 소유
> 파일만 고치고 나머지는 읽기만 한다. 설계 결정은 마음대로 진행하지 말고 물어보면서.
> 시스템의 이름·식별자는 영어, 한글은 화면 문장에만.

- **S1**: "…S1 `ONTOLOGY`. 첫 일: `layerS2_profiles.yaml` 의 DRAFT 5개(dressing·dip·
  condiment·soup·beverage_milk) 파라미터 범위를 표로 보여 주고 확인받아."
- **S2**: "…S2 `INGREDIENT`. 첫 일: `data/typical_review_new.xlsx` 를 `typical_review.xlsx`
  로 바꾸고, 걸린 행 234건 중 '자릿수' 말고 남은 것부터 판정을 받아. `ANTHROPIC_API_KEY`
  는 사용자 환경변수에 있다."
- **S3**: "…S3 `MODEL`. 첫 일: 팔레트 `통상근거` 의 dose_response(linear·threshold·
  saturating)를 Γ₀ 에 어떻게 반영할지 설계안을 내고 물어봐. 온톨로지 값은 고치지 않는다."
- **S4**: "…S4 `INTAKE`. 첫 일: Output 4(identity·unresolved)·5·6 의 YAML 형식 초안을
  `projects/RV_rice_milk/` 에 만들어 보여 줘. LEXICON 에 낱말을 더하지 말고 '없는 말'
  목록으로 넘겨."
- **S5**: "…S5 `APP`. 첫 일: 미푸시 커밋을 확인하고 푸시, 그다음 화면에서 제품(RV_rice_milk)
  이 제형과 나란히 뜨는 것을 정리할 방안을 물어봐."
