"""Policy Resolver coordinating Policy Pins and Policy Overrides."""
from dataclasses import dataclass
from typing import List, Optional, Tuple

from app.core.clock import Clock, get_clock
from app.domain.enums import RiskCategory
from app.policy.override_resolver import OverrideResolver, PolicyOverride
from app.policy.pin_registry import PinRegistry, PolicyPin
from app.schemas.operation import OperationPayload


@dataclass
class PolicyResolutionResult:
    final_category: RiskCategory
    override_applied: bool
    override_category: Optional[int]
    override_reason: Optional[str]
    policy_pin_applied: bool
    applied_pin_id: Optional[str]
    resolution_reasons: List[str]


class PolicyResolver:
    """Coordinates active policy pins and overrides to produce the final risk category."""

    def __init__(
        self,
        override_resolver: Optional[OverrideResolver] = None,
        pin_registry: Optional[PinRegistry] = None,
        clock: Optional[Clock] = None,
    ):
        self.override_resolver = override_resolver or OverrideResolver(clock=clock)
        self.pin_registry = pin_registry or PinRegistry(clock=clock)
        self._clock = clock

    @property
    def clock(self) -> Clock:
        return self._clock or get_clock()

    def resolve(
        self,
        rubric_category: RiskCategory,
        operation: OperationPayload,
    ) -> PolicyResolutionResult:
        """Resolve policy pins and policy overrides against the rubric category.

        Evaluation order:
        1. Check active/usable policy pins that apply to this operation or policy
        2. Check active policy overrides
        """
        current_category = rubric_category
        reasons: List[str] = []
        now = self.clock.now()

        applied_pin_id: Optional[str] = None
        policy_pin_applied = False

        # 1. Policy Pin check
        # Check if operation references a specific pin in payload or if an active pin matches policy/operation
        pin_id = operation.payload.get("pinId") or operation.payload.get("policyPinId")
        if pin_id:
            pin = self.pin_registry.get_pin(str(pin_id))
            if pin and self.pin_registry.is_usable(pin, now):
                policy_pin_applied = True
                applied_pin_id = pin.pin_id
                status = self.pin_registry.compute_status(pin, now)
                reasons.append(
                    f"Active Policy Pin '{pin.pin_id}' applied (Policy: {pin.policy_id}, Status: {status.value}, Reason: {pin.reason})"
                )
                # If policy pin enforces strict critical policy (e.g. policyId contains CRITICAL or STRICT_CAT_4)
                if "CRITICAL" in pin.policy_id.upper() or "CAT_4" in pin.policy_id.upper() or "STRICT" in pin.policy_id.upper():
                    current_category = RiskCategory.CRITICAL
                    reasons.append(f"Policy Pin '{pin.pin_id}' ({pin.policy_id}) enforced Category 4")
            elif pin:
                status = self.pin_registry.compute_status(pin, now)
                reasons.append(f"Policy Pin '{pin.pin_id}' present but unusable (Status: {status.value})")

        # 2. Check general active policy pins if no specific pinId was passed
        if not policy_pin_applied:
            for pin in self.pin_registry.pins:
                if self.pin_registry.is_usable(pin, now):
                    # Check if pin matches operation policy
                    target_policy = operation.payload.get("policyId")
                    if target_policy and str(target_policy).upper() == pin.policy_id.upper():
                        policy_pin_applied = True
                        applied_pin_id = pin.pin_id
                        status = self.pin_registry.compute_status(pin, now)
                        reasons.append(
                            f"Matched Policy Pin '{pin.pin_id}' for policy '{pin.policy_id}' (Status: {status.value})"
                        )
                        if "CRITICAL" in pin.policy_id.upper() or "CAT_4" in pin.policy_id.upper() or "STRICT" in pin.policy_id.upper():
                            current_category = RiskCategory.CRITICAL
                            reasons.append(f"Policy Pin '{pin.pin_id}' enforced Category 4")
                        break

        # 3. Evaluate Policy Overrides
        (
            final_cat,
            override_applied,
            override_category,
            override_reason,
            override_reasons,
        ) = self.override_resolver.resolve(current_category, operation)

        reasons.extend(override_reasons)

        return PolicyResolutionResult(
            final_category=final_cat,
            override_applied=override_applied,
            override_category=override_category,
            override_reason=override_reason,
            policy_pin_applied=policy_pin_applied,
            applied_pin_id=applied_pin_id,
            resolution_reasons=reasons,
        )
