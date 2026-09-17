from .ontology import Ontology
from .projection import project, apply_reformulation_pattern, Projection
from .filters import DietaryFilter, substitutes_for
from .learn import load_dataset, PLS, GPR, loo_compare
from .structured import StructuredModel, prior_vector, loo_structured
from .active_design import recommend_directions, propose_doe
# 2026-09-17 패키지에서 뺌 → _legacy/ (이유는 _legacy/README.md):
#   cypher.py    그래프 통째 내보내기 — RULES E4
#   optimize.py  시뮬레이터 + 합성 코퍼스 + 라운드별 GP + 획득함수 루프 — 특허 경계 §6.1
__all__ = ["Ontology", "project", "apply_reformulation_pattern", "Projection",
           "DietaryFilter", "substitutes_for",
           "load_dataset", "PLS", "GPR", "loo_compare",
           "StructuredModel", "prior_vector", "loo_structured",
           "recommend_directions", "propose_doe"]
