"""Dynamic Rubric Rule Engine.

Evaluates operation payload and attributes against configured dynamic rules,
supporting priority-based escalation and explainability.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from app.domain.enums import RiskCategory, RuleAction
from app.schemas.operation import OperationPayload


@dataclass
class DynamicRule:
    """Dynamic rule definition."""
    rule_id: str
    name: str
    conditions: Dict[str, Any]
    result_action: RuleAction
    target_category: int
    priority: int = 100
    enabled: bool = True


class DynamicRubricEngine:
    """Evaluates dynamic rules against an operation payload."""

    def __init__(self, rules: Optional[List[DynamicRule]] = None):
        self.rules: List[DynamicRule] = rules or []

    def set_rules(self, rules: List[DynamicRule]) -> None:
        self.rules = rules

    def _extract_value(self, operation: OperationPayload, key: str) -> Any:
        """Extract a value from top-level operation or nested payload."""
        # Check direct attributes
        if key == "operationType":
            return operation.operationType
        if key == "scope":
            return operation.scope.value
        if key == "reversibility":
            return operation.reversibility.value
        if key == "persistence":
            return operation.persistence.value
        if key == "operationId":
            return operation.operationId

        # Check payload.field or field in payload
        if key.startswith("payload."):
            sub_key = key.split("payload.", 1)[1]
            return self._get_nested_val(operation.payload, sub_key)

        # Fallback to direct key in payload
        if key in operation.payload:
            return operation.payload[key]

        return None

    def _get_nested_val(self, data: Dict[str, Any], path: str) -> Any:
        parts = path.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    def _matches_condition(self, actual_value: Any, expected_value: Any) -> bool:
        """Evaluate if an extracted value satisfies the rule condition."""
        if actual_value is None:
            return False

        # Case-insensitive comparison for strings
        if isinstance(actual_value, str) and isinstance(expected_value, str):
            return actual_value.strip().upper() == expected_value.strip().upper()

        # List containment (expected is list)
        if isinstance(expected_value, list):
            if isinstance(actual_value, str):
                return actual_value.upper() in [str(x).upper() for x in expected_value]
            return actual_value in expected_value

        # Dict with operators: e.g. {"gte": 1000}, {"in": [...]}, {"eq": "..."}
        if isinstance(expected_value, dict):
            for op, val in expected_value.items():
                if op in ("eq", "equals"):
                    if not self._matches_condition(actual_value, val):
                        return False
                elif op in ("gte", ">="):
                    if not (actual_value >= val):
                        return False
                elif op in ("lte", "<="):
                    if not (actual_value <= val):
                        return False
                elif op in ("gt", ">"):
                    if not (actual_value > val):
                        return False
                elif op in ("lt", "<"):
                    if not (actual_value < val):
                        return False
                elif op in ("in", "contains"):
                    if isinstance(actual_value, list):
                        if val not in actual_value:
                            return False
                    elif str(actual_value).upper() not in [str(x).upper() for x in val]:
                        return False
            return True

        return actual_value == expected_value

    def evaluate_rule(self, rule: DynamicRule, operation: OperationPayload) -> bool:
        """Check if a single rule matches the operation."""
        if not rule.enabled:
            return False

        for cond_key, expected_val in rule.conditions.items():
            actual_val = self._extract_value(operation, cond_key)
            if not self._matches_condition(actual_val, expected_val):
                return False

        return True

    def evaluate(
        self, base_category: RiskCategory, operation: OperationPayload
    ) -> Tuple[RiskCategory, List[str], List[str]]:
        """Evaluate all active dynamic rules and produce updated category.

        Returns:
            (resulting_category, matched_rule_ids, explanation_lines)
        """
        # Sort active rules by priority descending
        active_rules = sorted(
            [r for r in self.rules if r.enabled],
            key=lambda r: r.priority,
            reverse=True,
        )

        current_category = base_category.value
        matched_rule_ids: List[str] = []
        explanations: List[str] = []

        for rule in active_rules:
            if self.evaluate_rule(rule, operation):
                matched_rule_ids.append(rule.rule_id)
                target_cat = rule.target_category

                if rule.result_action in (RuleAction.SET_MIN_CATEGORY, RuleAction.ESCALATE_TO):
                    if target_cat > current_category:
                        explanations.append(
                            f"Dynamic Rule '{rule.rule_id}' ({rule.name}) matched: Escalated category from {current_category} to {target_cat}"
                        )
                        current_category = max(current_category, target_cat)
                    else:
                        explanations.append(
                            f"Dynamic Rule '{rule.rule_id}' ({rule.name}) matched (Priority {rule.priority}), but category {current_category} already >= {target_cat}"
                        )
                elif rule.result_action == RuleAction.SET_EXACT_CATEGORY:
                    explanations.append(
                        f"Dynamic Rule '{rule.rule_id}' ({rule.name}) matched: Forced category to {target_cat}"
                    )
                    current_category = target_cat

        return RiskCategory.from_value(current_category), matched_rule_ids, explanations
