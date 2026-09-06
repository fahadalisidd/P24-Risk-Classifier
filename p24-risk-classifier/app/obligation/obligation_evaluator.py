"""Obligation Evaluator.

CRITICAL ARCHITECTURAL RULE:
Obligations are evaluated ONLY AFTER the final risk category has been determined.
Schema validation must never validate obligation presence upfront.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.domain.enums import RiskCategory
from app.schemas.operation import OperationPayload


@dataclass
class ObligationEvaluationResult:
    required_obligations: List[str]
    obligations_satisfied: bool
    missing_obligations: List[str]


class ObligationEvaluator:
    """Evaluates whether required obligations are satisfied for a classified risk category."""

    def __init__(self, category_obligations_map: Optional[Dict[RiskCategory, List[str]]] = None):
        self.category_obligations_map = category_obligations_map or {
            RiskCategory.LOW: [],
            RiskCategory.MEDIUM: ["justification"],
            RiskCategory.HIGH: ["justification", "approval"],
            RiskCategory.CRITICAL: ["approval", "justification", "rollbackPlan"],
        }

    def get_required_obligations(self, category: RiskCategory) -> List[str]:
        """Determine required obligations for the given category."""
        return list(self.category_obligations_map.get(category, []))

    def is_field_present(self, payload: Dict[str, Any], field_name: str) -> bool:
        """Check if an obligation field is present and non-empty in payload."""
        if field_name not in payload:
            # Check inside 'obligations' sub-dictionary if user passed nested obligations
            if "obligations" in payload and isinstance(payload["obligations"], dict):
                return self.is_field_present(payload["obligations"], field_name)
            return False

        val = payload[field_name]
        if val is None:
            return False
        if isinstance(val, str) and not val.strip():
            return False
        if isinstance(val, (list, dict)) and len(val) == 0:
            return False
        return True

    def evaluate(
        self, final_category: RiskCategory, operation: OperationPayload
    ) -> ObligationEvaluationResult:
        """Evaluate obligations for the classified risk category."""
        required = self.get_required_obligations(final_category)
        missing: List[str] = []

        for req in required:
            if not self.is_field_present(operation.payload, req):
                missing.append(req)

        satisfied = len(missing) == 0

        return ObligationEvaluationResult(
            required_obligations=required,
            obligations_satisfied=satisfied,
            missing_obligations=missing,
        )
