# 04 척도 — 척도의 0 은 원점, 한 단계는 한 차이. 숫자 결정은 사용자 승인 뒤

뼈대 2026-09-12 (S1).

## 이 장이 정하는 것과 아닌 것

척도는 세 겹이다.

| 겹 | 무엇 | 누가 | 어디 |
|---|---|---|---|
| **어휘** | 척도의 이름(`diff_7` = ±3), 0 의 뜻(원점 = 기준 제품 또는 첫 시제품), 앵커 문장의 형식(어느 축에 몇 개, 어떤 문장 꼴), `tier` · `goal` · `evidence_required` 의 값 | S1 — 문법 | 이 장 |
| **수치** | 한 단계가 몇 σ 인가(1 단계 ≈ 1 JND), `RANGE_TO_SD` 4.0 → 2.0, 반복 없이 σ 를 어떻게 잡나 | S3 가 제안, **사용자 승인** | `docs/척도정의_전략.md` (승인 대기) |
| **절차** | 패널 몇 명, 반복 몇 번, 숙성 시료 언제 | 사용자(실험실) | Output 8 안내문 |

S1 이 정하는 것은 첫 줄뿐이다. 둘째 줄은 이미 문서가 있고 승인을 기다린다 — 문법은
그 결론을 **가리키기만** 한다. 셋째 줄은 문법이 아니다.

## 지금 있는 것 (재 봄 2026-09-12)

    scale_type: diff_7            AXIS_CARD 112장 전부
    method: benchmark_difference  82장 / difference_from_reference 30장 — 같은 것 (01장 V5)
    benchmark: current_recipe     110장 / fresh_sample 2장
    ko.anchors:                   -3 · 0 · +3 세 문장 — 제형 카드 대부분이 가짐 (top-level anchors 는 1장)
    tier: core 42 / monitored 70
    default_goal: maintain 80 / minimize 30 / target 2
    evidence_required: sample 95 / sample_aged 17
    docs/앵커설정_리서치.md        앵커 문장 연구

## 현황 · 규칙 · 예 · 검사 · 판단

(01·02 뒤에 채운다. 규칙 후보: 앵커는 축마다 -3 · 0 · +3 세 문장, 0 은 원점 서술이 아니라
"기준과 같다", 앵커 문장에 재료 이름이 오지 않는다)
