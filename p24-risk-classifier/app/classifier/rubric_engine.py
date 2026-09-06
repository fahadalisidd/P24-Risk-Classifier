"""Rubric Engine coordinating static and dynamic risk classification."""
from dataclasses import dataclass
from typing import List, Optional, Tuple

from app.classifier.static_rubric import StaticRubric
from app.classifier.dynamic_rubric import DynamicRubricEngine, DynamicRule
from app.domain.enums import RiskCategory
from app.schemas.operation import OperationPayload


@dataclass
class RubricEvaluationResult:
    risk_score: int
    base_category: RiskCategory
    rubric_category: RiskCategory
    matched_rules: List[str]
    classification_reasons: List[str]


class RubricEngine:
    """Primary rubric evaluation engine combining static scoring and dynamic rules."""

    def __init__(
        self,
        static_rubric: Optional[StaticRubric] = None,
        dynamic_engine: Optional[DynamicRubricEngine] = None,
    ):
        self.static_rubric = static_rubric or StaticRubric()
        self.dynamic_engine = dynamic_engine or DynamicRubricEngine()

    def evaluate(self, operation: OperationPayload) -> RubricEvaluationResult:
        """Run complete rubric classification for an operation."""
        # 1. Evaluate Static Rubric
        score, base_category, static_reasons = self.static_rubric.evaluate(
            scope=operation.scope,
            reversibility=operation.reversibility,
            persistence=operation.persistence,
        )

        reasons = list(static_reasons)

        # 2. Evaluate Dynamic Rules
        rubric_category, matched_rules, dynamic_reasons = self.dynamic_engine.evaluate(
            base_category=base_category,
            operation=operation,
        )

        reasons.extend(dynamic_reasons)

        return RubricEvaluationResult(
            risk_score=score,
            base_category=base_category,
            rubric_category=rubric_category,
            matched_rules=matched_rules,
            classification_reasons=reasons,
        )
