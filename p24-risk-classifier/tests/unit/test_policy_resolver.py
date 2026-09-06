"""Unit tests for combined PolicyResolver."""
from datetime import datetime, timezone
import pytest

from app.core.clock import ControllableClock
from app.domain.enums import Scope, Reversibility, Persistence, RiskCategory
from app.policy.override_resolver import OverrideResolver, PolicyOverride
from app.policy.pin_registry import PinRegistry, PolicyPin
from app.policy.policy_resolver import PolicyResolver
from app.schemas.operation import OperationPayload


class TestPolicyResolver:
    @pytest.fixture
    def test_clock(self):
        return ControllableClock(datetime(2026, 8, 25, 12, 0, 0, tzinfo=timezone.utc))

    def test_policy_pin_enforces_category_4(self, test_clock):
        pin = PolicyPin(
            pin_id="pin-crit",
            policy_id="STRICT_CRITICAL_POLICY",
            reason="High risk period freeze",
            review_date=datetime(2026, 8, 20, 0, 0, 0, tzinfo=timezone.utc),
            expires_at=datetime(2026, 9, 1, 0, 0, 0, tzinfo=timezone.utc),
            enabled=True,
        )
        pin_reg = PinRegistry(pins=[pin], clock=test_clock)
        resolver = PolicyResolver(pin_registry=pin_reg, clock=test_clock)

        op = OperationPayload(
            operationId="op-pin-1",
            operationType="READ",
            scope=Scope.LOCAL,
            reversibility=Reversibility.REVERSIBLE,
            persistence=Persistence.TEMPORARY,
            payload={"pinId": "pin-crit"},
        )

        res = resolver.resolve(RiskCategory.LOW, op)
        assert res.final_category == RiskCategory.CRITICAL
        assert res.policy_pin_applied is True
        assert res.applied_pin_id == "pin-crit"
