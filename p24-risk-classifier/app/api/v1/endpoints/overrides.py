"""Policy override endpoints."""
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.clock import get_clock
from app.db.session import get_db
from app.domain.models import PolicyOverrideModel
from app.schemas.policy import PolicyOverrideCreate, PolicyOverrideResponse

router = APIRouter(prefix="/policies/overrides", tags=["Policy Overrides"])


@router.get(
    "",
    response_model=List[PolicyOverrideResponse],
    summary="List all policy overrides",
)
def list_overrides(
    db: Session = Depends(get_db),
) -> List[PolicyOverrideResponse]:
    db_overrides = db.query(PolicyOverrideModel).all()
    return [
        PolicyOverrideResponse(
            id=o.id,
            name=o.name,
            conditions=o.conditions,
            forcedCategory=o.forced_category,
            reason=o.reason,
            enabled=o.enabled,
            createdAt=o.created_at,
            expiresAt=o.expires_at,
        )
        for o in db_overrides
    ]


@router.post(
    "",
    response_model=PolicyOverrideResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a policy override",
)
def create_override(
    override_in: PolicyOverrideCreate,
    db: Session = Depends(get_db),
) -> PolicyOverrideResponse:
    now = get_clock().now()
    new_override = PolicyOverrideModel(
        name=override_in.name,
        conditions=override_in.conditions,
        forced_category=override_in.forcedCategory,
        reason=override_in.reason,
        enabled=override_in.enabled,
        created_at=now,
        expires_at=override_in.expiresAt,
    )
    db.add(new_override)
    db.commit()
    db.refresh(new_override)

    return PolicyOverrideResponse(
        id=new_override.id,
        name=new_override.name,
        conditions=new_override.conditions,
        forcedCategory=new_override.forced_category,
        reason=new_override.reason,
        enabled=new_override.enabled,
        createdAt=new_override.created_at,
        expiresAt=new_override.expires_at,
    )
