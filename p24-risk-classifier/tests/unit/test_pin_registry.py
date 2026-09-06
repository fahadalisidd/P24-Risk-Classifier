"""Unit tests for Policy Pin Registry and Controllable Clock."""
from datetime import datetime, timezone, timedelta
import pytest

from app.core.clock import ControllableClock
from app.domain.enums import PinStatus
from app.policy.pin_registry import PinRegistry, PolicyPin


class TestPinRegistry:
    @pytest.fixture
    def base_clock(self):
        return ControllableClock(datetime(2026, 8, 25, 12, 0, 0, tzinfo=timezone.utc))

    def test_pin_status_lifecycle_with_controllable_clock(self, base_clock):
        pin = PolicyPin(
            pin_id="pin-100",
            policy_id="PROD_POLICY",
            reason="Temporary production rule pin",
            review_date=datetime(2026, 8, 20, 0, 0, 0, tzinfo=timezone.utc),
            expires_at=datetime(2026, 9, 1, 0, 0, 0, tzinfo=timezone.utc),
            enabled=True,
        )
        registry = PinRegistry(pins=[pin], clock=base_clock)

        # 1. Before review date (2026-08-10)
        base_clock.set_time(datetime(2026, 8, 10, 12, 0, 0, tzinfo=timezone.utc))
        assert registry.compute_status(pin) == PinStatus.ACTIVE
        assert registry.is_usable(pin) is True
        assert registry.calculate_days_overdue(pin) == 0

        # 2. After review date but before expiry (2026-08-25) -> REVIEW_OVERDUE but still USABLE
        base_clock.set_time(datetime(2026, 8, 25, 12, 0, 0, tzinfo=timezone.utc))
        assert registry.compute_status(pin) == PinStatus.REVIEW_OVERDUE
        assert registry.is_usable(pin) is True
        assert registry.calculate_days_overdue(pin) == 5  # 5 days past 2026-08-20

        # 3. After expiry date (2026-09-05) -> EXPIRED and NOT USABLE
        base_clock.set_time(datetime(2026, 9, 5, 12, 0, 0, tzinfo=timezone.utc))
        assert registry.compute_status(pin) == PinStatus.EXPIRED
        assert registry.is_usable(pin) is False

        # 4. Disabled pin -> DISABLED
        pin.enabled = False
        assert registry.compute_status(pin) == PinStatus.DISABLED
        assert registry.is_usable(pin) is False

    def test_review_report_generation(self, base_clock):
        pin1 = PolicyPin(
            pin_id="pin-overdue",
            policy_id="POLICY_A",
            reason="Overdue pin",
            review_date=datetime(2026, 8, 15, 0, 0, 0, tzinfo=timezone.utc),
            expires_at=datetime(2026, 9, 15, 0, 0, 0, tzinfo=timezone.utc),
            enabled=True,
        )
        pin2 = PolicyPin(
            pin_id="pin-active",
            policy_id="POLICY_B",
            reason="Future review pin",
            review_date=datetime(2026, 9, 1, 0, 0, 0, tzinfo=timezone.utc),
            expires_at=datetime(2026, 10, 1, 0, 0, 0, tzinfo=timezone.utc),
            enabled=True,
        )
        registry = PinRegistry(pins=[pin1, pin2], clock=base_clock)

        # Time is 2026-08-25 -> pin1 is 10 days overdue, pin2 is not overdue
        base_clock.set_time(datetime(2026, 8, 25, 12, 0, 0, tzinfo=timezone.utc))
        report = registry.get_review_report()

        assert len(report) == 1
        assert report[0]["pinId"] == "pin-overdue"
        assert report[0]["status"] == PinStatus.REVIEW_OVERDUE
        assert report[0]["daysOverdue"] == 10
