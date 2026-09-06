"""Policy Pin Registry.

Manages temporary policy pins, evaluating lifecycle status (ACTIVE, REVIEW_OVERDUE, EXPIRED, DISABLED)
and generating pin review reports using a controllable clock.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from app.core.clock import Clock, get_clock
from app.domain.enums import PinStatus


@dataclass
class PolicyPin:
    pin_id: str
    policy_id: str
    reason: str
    review_date: datetime
    expires_at: datetime
    enabled: bool = True
    created_at: Optional[datetime] = None


class PinRegistry:
    """Registry managing policy pins and their review statuses."""

    def __init__(self, pins: Optional[List[PolicyPin]] = None, clock: Optional[Clock] = None):
        self.pins: List[PolicyPin] = pins or []
        self._clock = clock

    @property
    def clock(self) -> Clock:
        return self._clock or get_clock()

    def set_pins(self, pins: List[PolicyPin]) -> None:
        self.pins = pins

    def get_pin(self, pin_id: str) -> Optional[PolicyPin]:
        for pin in self.pins:
            if pin.pin_id == pin_id:
                return pin
        return None

    def compute_status(self, pin: PolicyPin, now: Optional[datetime] = None) -> PinStatus:
        """Compute pin status based on current time."""
        current_time = now or self.clock.now()

        if not pin.enabled:
            return PinStatus.DISABLED

        review_dt = pin.review_date
        if review_dt.tzinfo is None:
            review_dt = review_dt.replace(tzinfo=timezone.utc)

        exp_dt = pin.expires_at
        if exp_dt.tzinfo is None:
            exp_dt = exp_dt.replace(tzinfo=timezone.utc)

        if current_time > exp_dt:
            return PinStatus.EXPIRED

        if current_time > review_dt:
            return PinStatus.REVIEW_OVERDUE

        return PinStatus.ACTIVE

    def is_usable(self, pin: PolicyPin, now: Optional[datetime] = None) -> bool:
        """A pin is usable if enabled and not expired."""
        status = self.compute_status(pin, now)
        return status in (PinStatus.ACTIVE, PinStatus.REVIEW_OVERDUE)

    def calculate_days_overdue(self, pin: PolicyPin, now: Optional[datetime] = None) -> int:
        """Calculate days overdue past review date (0 if not overdue)."""
        current_time = now or self.clock.now()
        review_dt = pin.review_date
        if review_dt.tzinfo is None:
            review_dt = review_dt.replace(tzinfo=timezone.utc)

        if current_time <= review_dt:
            return 0

        diff = current_time - review_dt
        return max(0, int(diff.total_seconds() // 86400))

    def get_review_report(self, now: Optional[datetime] = None) -> List[dict]:
        """Generate report items for pins whose review date has passed."""
        current_time = now or self.clock.now()
        report_items = []

        for pin in self.pins:
            status = self.compute_status(pin, current_time)
            # Include pins that are REVIEW_OVERDUE or EXPIRED if past review date
            review_dt = pin.review_date
            if review_dt.tzinfo is None:
                review_dt = review_dt.replace(tzinfo=timezone.utc)

            if current_time > review_dt:
                days_overdue = self.calculate_days_overdue(pin, current_time)
                report_items.append({
                    "pinId": pin.pin_id,
                    "policyId": pin.policy_id,
                    "reviewDate": pin.review_date,
                    "expiresAt": pin.expires_at,
                    "status": status,
                    "daysOverdue": days_overdue,
                    "reason": pin.reason,
                })

        return report_items
