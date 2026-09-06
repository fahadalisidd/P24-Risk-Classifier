"""Policy pin endpoints and pin review report."""
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.clock import get_clock
from app.db.session import get_db
from app.domain.models import PolicyPinModel
from app.policy.pin_registry import PinRegistry, PolicyPin
from app.schemas.policy import (
    PolicyPinCreate,
    PolicyPinResponse,
    PinReviewReportResponse,
    PinReviewReportItem,
)

router = APIRouter(prefix="/policies/pins", tags=["Policy Pins"])


@router.get(
    "/review-report",
    response_model=PinReviewReportResponse,
    summary="Get policy pins review report",
    description="Identifies policy pins whose review date has passed, along with days overdue and status.",
)
def get_pin_review_report(
    db: Session = Depends(get_db),
) -> PinReviewReportResponse:
    clock = get_clock()
    now = clock.now()

    db_pins = db.query(PolicyPinModel).all()
    pins = [
        PolicyPin(
            pin_id=p.pin_id,
            policy_id=p.policy_id,
            reason=p.reason,
            review_date=p.review_date,
            expires_at=p.expires_at,
            enabled=p.enabled,
            created_at=p.created_at,
        )
        for p in db_pins
    ]

    registry = PinRegistry(pins=pins, clock=clock)
    raw_report = registry.get_review_report(now)

    items = [PinReviewReportItem.model_validate(item) for item in raw_report]

    return PinReviewReportResponse(
        reportGeneratedAt=now,
        overduePinCount=len(items),
        expiredReviewPins=items,
    )


@router.get(
    "",
    response_model=List[PolicyPinResponse],
    summary="List all policy pins",
)
def list_pins(
    db: Session = Depends(get_db),
) -> List[PolicyPinResponse]:
    clock = get_clock()
    now = clock.now()
    db_pins = db.query(PolicyPinModel).all()

    registry = PinRegistry(clock=clock)
    results = []
    for p in db_pins:
        domain_pin = PolicyPin(
            pin_id=p.pin_id,
            policy_id=p.policy_id,
            reason=p.reason,
            review_date=p.review_date,
            expires_at=p.expires_at,
            enabled=p.enabled,
            created_at=p.created_at,
        )
        status_val = registry.compute_status(domain_pin, now)
        results.append(
            PolicyPinResponse(
                pinId=p.pin_id,
                policyId=p.policy_id,
                reason=p.reason,
                reviewDate=p.review_date,
                expiresAt=p.expires_at,
                enabled=p.enabled,
                createdAt=p.created_at,
                status=status_val,
            )
        )
    return results


@router.post(
    "",
    response_model=PolicyPinResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new policy pin",
)
def create_pin(
    pin_in: PolicyPinCreate,
    db: Session = Depends(get_db),
) -> PolicyPinResponse:
    clock = get_clock()
    now = clock.now()

    new_pin = PolicyPinModel(
        pin_id=pin_in.pinId,
        policy_id=pin_in.policyId,
        reason=pin_in.reason,
        review_date=pin_in.reviewDate,
        expires_at=pin_in.expiresAt,
        enabled=pin_in.enabled,
        created_at=now,
    )
    db.add(new_pin)
    db.commit()
    db.refresh(new_pin)

    registry = PinRegistry(clock=clock)
    domain_pin = PolicyPin(
        pin_id=new_pin.pin_id,
        policy_id=new_pin.policy_id,
        reason=new_pin.reason,
        review_date=new_pin.review_date,
        expires_at=new_pin.expires_at,
        enabled=new_pin.enabled,
        created_at=new_pin.created_at,
    )
    status_val = registry.compute_status(domain_pin, now)

    return PolicyPinResponse(
        pinId=new_pin.pin_id,
        policyId=new_pin.policy_id,
        reason=new_pin.reason,
        reviewDate=new_pin.review_date,
        expiresAt=new_pin.expires_at,
        enabled=new_pin.enabled,
        createdAt=new_pin.created_at,
        status=status_val,
    )
