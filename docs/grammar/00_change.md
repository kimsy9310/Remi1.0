# 00 변화 규칙 — 고칠 때는 `--check` 먼저, 옛 이름은 지우지 않고 별칭으로 남긴다

뼈대 2026-09-12 (S1). 마지막에 채운다 — 흩어진 규칙(`CLAUDE.md` · 도구 docstring · YAML 머리 주석)을 모으는 정리다.

## 이 장이 정하는 것

용어 · 파라미터 · 제형 · 관계 · 카드를 **더하고 · 고치고 · 빼는 절차**.

    더할 때    도구로. --check 가 기본, --write 로만 쓴다. 두 번 돌려도 같다
    고칠 때    텍스트로 끼워 넣는다 (앵커 &id · 주석을 살리려고). safe_dump 금지
    뺄 때      지우지 않고 _deprecated_aliases.yaml 에 옛 → 새 대응을 남긴다
    재정의     LEXICON 은 redefined: 에 날짜와 이유. 옛 정의는 남긴다
    확신       새로 난 값은 confidence: draft. 사람이 본 뒤 low/medium/high
    이력       "왜" 를 그 자리에 적는다 — 이 저장소는 주석이 결정 기록이다

## Remi 1.1 이관 표 — 문법이 정했지만 지금 파일을 바꾸지 않는 것

| # | 무엇 | 어디 | 근거 | 걸리는 것 |
|---|---|---|---|---|
| 1 | `scoped_to_structure_class` · `active_in` → `scope` | INGREDIENT · AXIS_CARD | 01 V6 | 로더 |
| 2 | 점 스코프 `SC.a.b.c` → 파이프 | INGREDIENT 엣지 125건 | 01 V3 | 로더 `scopes` 별칭 |
| 3 | `term_id` · `percept` → `axis` | AXIS_CARD · R-1 | 01 V4 | 로더 · 앱 |
| 4 | `reliability` · `range_confidence` → `confidence` | AXIS_CARD · STRUCTURE | 01 V5 | |
| 5 | `method: difference_from_reference` → `benchmark_difference` | AXIS_CARD 30 | 01 V5 | |
| 6 | `IX.*` → `IN.*` 별칭 3건 | `_deprecated_aliases` | 01 V1 | |
| 7 | `sauce_ow` → `sauce` · `icecream` → `dessert_frozen` | 로더 · 카드 파일명 · 데이터 파일 · 앱 | 02 P3 | **사용자 판단** |
| 8 | `meta.structure` → `meta.profile` | product_card | 02 P1 | 어댑터 `_load_projects` |
| 9 | `derived_from` 표시명 → 키 | STRUCTURE 3건 | 02 P3 | |
| 10 | `SA.` `IX.` **삭제** — `_deprecated_aliases.yaml` 67 · 렉시콘 `legacy_map` 64 · 카드 주석 16 · C2 `flavor_interactions` 3 | 7 파일 148곳 | 01 §9 | 코드가 읽지 않음 — 안전 |
| 11 | `PO.*` 70건 → `P.*.axes` 로 접음 | RELATION → PARAMETER | 01 §1 | 로더 `relations_proxy` · 어댑터 |
| 12 | `LESSON.*` 19건 → 관찰 레코드 꼴 (`about` `observed` `statement`) | STRUCTURE constraints | 01 §6 | 검사 도구 |
| 20 | 보편 카드 · 축 카드 파일 삭제 → L 기본값 + 제형 `relevant_attributes`(평가 주의 흡수) + 제품 카드 | AXIS_CARD 7파일 · universal | 01 §8 | 로더 `load_cards` · 앱 16곳 |
| 21 | IN → `interactions` / `overlaps` 두 목록, `effect` → `direction` | RELATION | 01 §4 | S3 · B1 SCOPE |
| 22 | PO 없는 P 8개에 `axes` 채우기 (03장에서 내용) | PARAMETER | 01 §0 | S1 |
| 23 | **`ko` 필드 전부 제거** — L 216 · 제형 7 · ING 118 · 카드 106 → S4 번역표 `lexicon_map_<locale>` 로 | LEXICON · STRUCTURE · INGREDIENT · 카드 | RULES A8 | S4 · 앱 |
| 24 | 제형에 `ST` 명시(`ST.ambient` 포함), ST 네 값 | STRUCTURE · taxonomy | RULES B0 B4 B5 | 로더 |
| 25 | 로더 B5-1 특성 대신 맞추기 + 스코프 대장에 빌림 기록 | 로더 · `tools/scope_index.py` | RULES B5-1 C9 | S1 도구 · S3 |
| 26 | 가시성 세 등급 · 관련 노드 경계 | 앱 · API | RULES E4 E5 | S5 |
| 27 | 변형(버전) — 원점 = 현재 제품, 제약은 `x` 경계 | Output 5 · C1 | RULES B16 | S5 · S3 |
| 13 | `active_in` 삭제 · `P.scope: universal` 삭제 | AXIS_CARD 112 · PARAMETER 3 | 01 §9 | 로더 |
| 14 | `function_tags: [FT]` → `functions: [{function, weight}]` · 별칭 hack 77건 정리 | INGREDIENT | 01 §2 | S2 · 로더 RULE 1 |
| 15 | `flavor_profile.intensity` → `magnitude` · PO `monotone` → `direction` | INGREDIENT · P.axes | 01 §3 | |
| 16 | DC `components[].weight` → `magnitude` + `direction` 추가 | RELATION | 01 §5 | 로더 |
| 17 | IN 상관 7건(`pos_corr` `inverse_corr`) → P.axes 또는 note | RELATION | 01 §4 | S3 |
| 18 | RP 레코드 꼴 (`reduce` `keep` `compensate` `why`) | INGREDIENT | 01 §7 | S2 |
| 19 | `layerS_taxonomy.yaml` 신설, 로더 `scopes` 계산 | STRUCTURE · 로더 | 02 계층 | |
