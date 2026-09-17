# _legacy — 패키지에서 뺀 v1 모듈 (2026-09-17, S3)

import 되지 않는다. 기록용으로만 남긴다.

| 파일 | 왜 뺐나 |
|---|---|
| `cypher.py` | 온톨로지 그래프를 통째로 Neo4j 로 내보낸다. RULES E4 — 컴포넌트·크기·범위·파일은 "절대 보여 주거나 내보내지 않는다". |
| `optimize.py` | 시뮬레이터(`PriorResponseModel.measure(noisy=True)`) → 합성 코퍼스 → 라운드마다 GP 재적합 → 획득함수 argmax → 고정 라운드 반복. `docs/특허_경계_TuringLabs_모형.md` §6.1 이 "만들지 않는 것" 으로 정한 조합(B-1 · B-28). 어디서도 호출되지 않던 v1 코드다. E2 최적화는 `mixture.propose` 의 QP 에 밴드 제약(|ŷ−y_b| ≤ δ)을 더해 다시 설계한다 — 서로게이트·시뮬레이터·획득함수 없이. |
