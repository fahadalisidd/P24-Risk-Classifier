"""Unit tests for Policy Override Resolver."""
from datetime import datetime, timezone, timedelta
import pytest

from app.core.clock import ControllableClock
from app.domain.enums import Scope, Reversibility, Persistence, RiskCategory
from app.policy.override_resolver import OverrideResolver, PolicyOverride
from app.schemas.operation import OperationPayload


class TestOverrideResolver:
    @pytest.fixture
    def test_clock(self):
        return ControllableClock(datetime(2026, 8, 25, 12, 0, 0, tzinfo=timezone.utc))

    def test_policy_override_forces_category(self, test_clock):
        override = PolicyOverride(
            id="ov-1",
            name="Emergency Change Freeze",
            conditions={"payload.environment": "PRODUCTION"},
            forced_category=4,
            reason="Production emergency freeze policy",
            enabled=True,
            expires_at=datetime(2026, 9, 1, 0, 0, 0, tzinfo=timezone.utc),
        )
        resolver = OverrideResolver(overrides=[override], clock=test_clock)

        op = OperationPayload(
            operationId="op-10",
            operationType="UPDATE",
            scope=Scope.LOCAL,
            reversibility=Reversibility.REVERSIBLE,
            persistence=Persistence.TEMPORARY,
            payload={"environment": "PRODUCTION"},
        )

        final_cat, applied, cat_val, reason, reasons = resolver.resolve(RiskCategory.LOW, op)
        assert applied is True
        assert final_cat == RiskCategory.CRITICAL
        assert cat_val == 4
        assert reason == "Production emergency freeze policy"
        assert len(reasons) > 0

    def test_expired_override_is_ignored(self, test_clock):
        override = PolicyOverride(
            id="ov-expired",
            name="Old Override",
            conditions={"payload.environment": "PRODUCTION"},
            forced_category=4,
            reason="Old policy",
            enabled=True,
            expires_at=datetime(2026, 8, 20, 0, 0, 0, tzinfo=timezone.utc),  # Expired relative to 2026-08-25
        )
        resolver = OverrideResolver(overrides=[override], clock=test_clock)

        op = OperationPayload(
            operationId="op-11",
            operationType="UPDATE",
            scope=Scope.LOCAL,
            reversibility=Reversibility.REVERSIBLE,
            persistence=Persistence.TEMPORARY,
            payload={"environment": "PRODUCTION"},
        )

        final_cat, applied, _, _, _ = resolver.resolve(RiskCategory.LOW, op)
        assert applied is False
        assert final_cat == RiskCategory.LOW
