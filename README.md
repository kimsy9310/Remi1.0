# Remi

**식품 배합 포뮬레이터.** 사용자가 원하는 맛·식감·외관을 말하면, 그것을 감각
온톨로지의 말로 바꾸고, 재료가 감각을 어떻게 움직이는지에 대한 사전지식으로
첫 배합을 세운 뒤, **최소한의 실험으로** 목표에 닿는 배합을 찾는다.

    "덜 느끼하고 바디감은 그대로인 쌀음료"
        → 축: 기름짐 −1 · 바디감 0 (벤치마크 대비)
        → 사전: 해바라기유 ↓ 가 기름짐을 내리고 바디감도 내린다 / 잔탄검 ↑ 는 바디감만 올린다
        → 첫 배합 → 실험 → 실측으로 사전을 보정 → 다음 배합

핵심 아이디어 둘:

- **온톨로지가 사전(prior)이다.** 재료 → 물성 → 감각의 관계를 YAML 로 적어 두면
  모형이 그것을 `Γ₀`(누가 무엇을 움직이는가)와 `Λ`(그 믿음의 세기)로 읽는다.
  데이터가 없어도 첫 배합이 나오고, 데이터가 쌓이면 사전이 밀려난다.
- **관능은 벤치마크 대비 ±3 이다.** 절대 점수가 아니라 "기준 제품보다 얼마나"
  를 묻는다. 훈련 안 된 소수 패널로도 돌아가는 유일한 척도다.

---

## 빠른 시작

```bash
pip install -r requirements.txt
streamlit run app/main.py
```

윈도우는 `run.bat`. 앱은 두 화면이다 — 사이드바에서 고른다.

| 화면 | 누가 | 무엇 |
|---|---|---|
| **사용자** | 제품을 만드는 사람 | 단계형 인터뷰: ① 무엇을 만드나 → ② 어떻게 바꾸나(축 슬라이더) → ③ 무엇을 쓰나(재료) → 제안 |
| **전문가** | 데이터·온톨로지를 손보는 사람 | 5탭: 데이터 · 학습 · 제안 · 팔레트 · 실험 입력 |

`data/beverage_warmloop_260720.xlsx`(쌀음료 시제품 18건)가 들어 있어 바로 돌려볼 수 있다.

---

## 어떻게 돌아가나 — 알고리즘

기준 그림은 `Algorithm_Remi/1st_Draft_algorithm_remi.drawio`. 구간과 각 구간이
읽는 레이어는 [`docs/layer_boundaries.md`](docs/layer_boundaries.md).

| 구간 | 하는 일 | 상태 (2026-09-11) |
|---|---|---|
| **A** Intake | 사용자 문장을 API 가 flavor·texture·appearance 로 가르고 LEXICON 의 말로 치환 | 칩 인터뷰만. API 파싱 미구현 |
| **B** Target | 벤치마크와 목표를 축 카드 위에 ±3 으로 규정 | 카드 구조 완료 |
| **C** Feasibility | 공정 · 필수/금지 재료 · 미등록 재료 검색 · 범위 안에서 닿는가 | 공정 기록 1단계, 범위 완료. 검색·C5 미구현 |
| **D** Build & Learn | 사전으로 첫 배합 → 실측 기록 → 벤치마크 0 기준 해석 → DoE | 완료 (DoE 는 v1 잔재) |
| **E** Refit & Optimize | 재적합 · 최적화 배합 · 온톨로지 환류 | 부분 |

진행도 전체와 앞으로의 작업 분할은 [`docs/session_split.md`](docs/session_split.md).

---

## 지식 레이어 (`ontology_v2/layers/`, YAML 41개)

| 레이어 | 파일 | 담는 것 | ID |
|---|---|---|---|
| `LEXICON` | `layerL_lexicon.yaml` | 감각 용어 216개. 맥락 없는 정의 | `L.*` |
| `PARAMETER` | `layerA_parameters.yaml` | 물성 39개. 단위·측정법 | `P.*` |
| `INGREDIENT` | `layerC2_*.yaml` | 재료 118 · 기능군 24. 재료 → 물성/감각 엣지, 한계, 대체 | `ING.*` `FT.*` |
| `RELATION` | `layerR_seed.yaml` | 물성 → 감각 (R-1) 70건, 감각 ↔ 감각 (R-2) | `PO.*` `IN.*` |
| `STRUCTURE` | `layerS2_profiles.yaml` | 제형 9개 (아이스크림 · 클라우드/밀크형 음료 · 소스 · 드레싱 · 딥 · 현탁 · 양념 · 수프). 정의 파라미터·범위·필러 | `SC.*` `APP.*` |
| `AXIS_CARD` | `layerM_cards_<제형>.yaml` | 제형별 축 카드 — 이 축을 여기서 어떻게 읽고 점수 매기나. 제품 사이에 공유 | |
| `PRODUCT_CARD` | `projects/<제품>/product_card.yaml` | 제품당 한 장. 제형 카드에서 **벗어나는 것만** (정체성 축, tier·goal, 실측 열, 뺀 축) | |
| `PROCESS` | *(아직 없음)* | 공정. 파라미터 위의 두 번째 액추에이터 | |

정본 로더는 `ontology_v2/tests/loader_reference.py`, 엔진이 쓰는 어댑터는
`engine/formulator/v2adapter.py`. 두 층 카드는 어댑터가 합친다 — 제형 카드에
제품 카드의 `drop` · `axes` 를 얹는다.

**효과 크기에는 양이 없다.** `weak/medium/strong = 0.3/0.6/1.0` 은 "재료를 1 SD
움직였을 때 ±3 눈금에서 몇 칸" 이고, `1 SD = (상한 − 하한) / 2` 다. 그래서 재료
범위가 곧 사전의 단위다 ([`docs/bounds_strategy.md`](docs/bounds_strategy.md)).

---

## 재료 범위 — 팔레트 (`data/palette.xlsx`)

재료 × 제형 한 줄. 제안의 신뢰도를 정하는 표라 **정본은 엑셀**이고 사람이 본다.

| 열 | 뜻 |
|---|---|
| 프로파일 · 목적 · 슬롯 · 재료 · 온톨로지ID | 슬롯 = 기능군 = 모형의 변수 하나. 목적(저당 등)은 기본 행을 덮는다 |
| 등급 | 필수 / 권장 / 옵션 / 제한 / 제외 |
| **통상** · 통상출처 · 통상근거 | 이 제형에서 이 재료를 보통 얼마나 넣나. 2026-09-11 API 초안 958행 (`api_draft`) |
| **하한 · 상한** · 범위근거 | 감각 수용 구간. 하한 0(벌크 재료만 예외), 상한 = 오프노트가 시작하는 양. 사전의 단위이자 솔버의 경계 |
| 담당축 | 자동 — 이 재료가 움직이는 축과 방향 |

```bash
python tools/fill_typical_api.py            # 계획·비용만 (--check)
python tools/fill_typical_api.py --write    # Claude API 로 통상 사용량 초안 (ANTHROPIC_API_KEY 환경변수)
python tools/check_bounds.py                # 범위 규칙 R1~R5 검사
python tools/check_bounds.py --write        # 통상에서 범위 초안
```

API 키는 환경변수로만 읽는다. 파일·코드에 두지 않는다.

---

## 실측 데이터 (`data/*.xlsx`)

| 시트 | 내용 |
|---|---|
| `recipes` | `sample_id` · `is_benchmark` · `ing_*` (배합. 배치 그램이든 % 든 행마다 100 으로 정규화) |
| `sensory` | `sample_id` · `rep` · `sens_*` (벤치마크 대비 −3…+3. 벤치마크 자신은 전 축 0) |
| `dictionary` | `ing_*` 컬럼 → `ING.*` |
| `instrumental` | (선택) 물성 실측 |

`sens_*` 열과 `L.*` 축을 잇는 다리는 카드의 `legacy_column` 이라 새 제품은 카드만
쓰면 데이터가 붙는다. 빈 양식은 전문가 화면 ⑤ 탭에서 만든다.

한 바퀴: 양식 만들기 → 랩에서 채움 → 올리기 → ② 학습(사전 보정) → ③ 제안 → 제조·평가 → 다시.

---

## 저장소

```
app/            Streamlit
  main.py         화면 둘 (사용자 · 전문가 5탭)
  user_flow.py    사용자 단계형 인터뷰
  interview.py    온톨로지에서 질문 생성
  dataio.py       실측 xlsx → (X, Y)
  warmloop.py     사전 + 실측 → 보정 → 제안
  palette.py      palette.xlsx 로더
  process.py      공정 기록 1단계
  store.py        SQLite 실행 이력
engine/
  formulator/     mixture.py (혼합물 모형 y = Γᵀz, Σx = 100) · v2adapter.py (온톨로지 → 모형) · doe · learn · optimize
  selfcheck_v2.py     온톨로지 경로 44건
  selfcheck_model.py  엔진 수학 18건
ontology_v2/    layers/ (YAML 41) · tests/loader_reference.py (정본 로더)
projects/       제품 폴더. <제품>/product_card.yaml
tools/          온톨로지·팔레트를 고치는 도구. 전부 --check 가 기본, --write 로만 쓴다
docs/           전략·진단 문서
data/           실측 · 팔레트 · 검토표 (백업·DB 는 git 제외)
Algorithm_Remi/ 알고리즘 그림 (drawio)
```

---

## 검사

```bash
python engine/selfcheck_v2.py                    # 온톨로지 44건
python engine/selfcheck_model.py                 # 엔진 18건
python ontology_v2/tests/loader_reference.py     # 프로파일 로더
python tools/audit_axis_scope.py                 # 축 의존성 감사
python tools/check_bounds.py                     # 팔레트 범위
```

온톨로지나 팔레트를 고쳤으면 전부 돌린다. 작업 규칙은 [`CLAUDE.md`](CLAUDE.md).

---

## 새 제품 붙이기

1. 제형을 고른다. 없으면 `tools/add_application.py` 로 가장 가까운 제형에서 파생한다.
2. `projects/<제품>/product_card.yaml` 을 쓴다 — `meta.structure` 에 제형, 그리고
   제형 카드와 **다른 것만** (`drop`, `axes` 의 tier·goal·legacy_column, 정체성 축).
3. `python engine/selfcheck_v2.py` — 도달성이 걸리면 그 축을 움직이는 재료가 없다는
   뜻이다. INGREDIENT 엣지나 R-1 을 보탠다.
4. 팔레트에 재료 행이 없으면 `fill_typical_api` → `check_bounds --write`.

사례: `projects/RV_rice_milk/` (쌀음료, `beverage_milk` 위에 선다).

---

## 문서

| 문서 | 무엇 |
|---|---|
| [`docs/session_split.md`](docs/session_split.md) | 진행도와 세션 분할 (S1 ONTOLOGY · S2 INGREDIENT · S3 MODEL · S4 INTAKE · S5 APP) |
| [`docs/layer_boundaries.md`](docs/layer_boundaries.md) | 알고리즘 구간 × 레이어. 무엇을 읽고 무엇을 쓰나 |
| [`docs/bounds_strategy.md`](docs/bounds_strategy.md) | 재료 범위 = 사전의 단위. 통상·상한·하한 규칙과 실행 결과 |
| [`docs/척도정의_전략.md`](docs/척도정의_전략.md) | ±3 척도, `RANGE_TO_SD` |
| [`docs/축_의존성_검증전략.md`](docs/축_의존성_검증전략.md) | 축이 존재하는 다섯 이유 (보편·제형·재료·공정·엣지 결손) |
| [`docs/공정_전략.md`](docs/공정_전략.md) | 공정 기록과 PROCESS 레이어 |
| [`docs/상호작용_알고리즘.md`](docs/상호작용_알고리즘.md) | 초기 알고리즘 문서 (구간 번호는 drawio 가 최신) |

## 이력

v1 온톨로지(3층)와 초기 프로토타입은 `recovered_food_recipe_app/` 에 있다. v1 로더와
v2 온톨로지는 섞어 쓰지 않는다. 이 저장소가 정본이다.
