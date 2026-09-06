"""Policy Override Resolver.

Evaluates explicit policy overrides that can force a risk category.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.core.clock import Clock, get_clock
from app.domain.enums import RiskCategory
from app.schemas.operation import OperationPayload


@dataclass
class PolicyOverride:
    id: str
    name: str
    conditions: Dict[str, Any]
    forced_category: int
    reason: str
    enabled: bool = True
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class OverrideResolver:
    """Evaluates whether any active policy overrides apply to an operation."""

    def __init__(self, overrides: Optional[List[PolicyOverride]] = None, clock: Optional[Clock] = None):
        self.overrides = overrides or []
        self._clock = clock

    @property
    def clock(self) -> Clock:
        return self._clock or get_clock()

    def set_overrides(self, overrides: List[PolicyOverride]) -> None:
        self.overrides = overrides

    def _extract_value(self, operation: OperationPayload, key: str) -> Any:
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

        if key.startswith("payload."):
            sub = key.split("payload.", 1)[1]
            return operation.payload.get(sub)

        if key in operation.payload:
            return operation.payload[key]

        return None

    def _matches(self, operation: OperationPayload, conditions: Dict[str, Any]) -> bool:
        if not conditions:
            # An empty condition override applies to all matching policy scope if configured
            return True

        for k, expected in conditions.items():
            actual = self._extract_value(operation, k)
            if actual is None:
                return False
            if isinstance(actual, str) and isinstance(expected, str):
                if actual.strip().upper() != expected.strip().upper():
                    return False
            elif actual != expected:
                return False
        return True

    def resolve(
        self, current_category: RiskCategory, operation: OperationPayload
    ) -> Tuple[RiskCategory, bool, Optional[int], Optional[str], List[str]]:
        """Resolve policy overrides against the operation.

        Returns:
            (final_category, override_applied, override_category, override_reason, reasons)
        """
        now = self.clock.now()
        reasons: List[str] = []

        for override in self.overrides:
            if not override.enabled:
                continue

            # Check expiration
            if override.expires_at is not None:
                exp = override.expires_at
                if exp.tzinfo is None:
                    from datetime import timezone
                    exp = exp.replace(tzinfo=timezone.utc)
                if now > exp:
                    continue

            if self._matches(operation, override.conditions):
                forced_cat = RiskCategory.from_value(override.forced_category)
                reasons.append(
                    f"Policy Override '{override.name}' applied (Forced Category {forced_cat.value}, Reason: {override.reason})"
                )
                return forced_cat, True, forced_cat.value, override.reason, reasons

        return current_category, False, None, None, reasons
