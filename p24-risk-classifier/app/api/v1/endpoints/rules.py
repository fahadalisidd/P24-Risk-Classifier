"""Dynamic rubric rule management endpoints."""
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.clock import get_clock
from app.db.session import get_db
from app.domain.enums import RuleAction
from app.domain.models import RiskRuleModel
from app.schemas.policy import DynamicRuleCreate, DynamicRuleResponse

router = APIRouter(prefix="/rules", tags=["Dynamic Rubric Rules"])


@router.get(
    "",
    response_model=List[DynamicRuleResponse],
    summary="List all dynamic rubric rules",
)
def list_rules(
    db: Session = Depends(get_db),
) -> List[DynamicRuleResponse]:
    db_rules = db.query(RiskRuleModel).order_by(RiskRuleModel.priority.desc()).all()
    return [
        DynamicRuleResponse(
            id=r.id,
            ruleId=r.rule_id,
            name=r.name,
            conditions=r.conditions,
            resultAction=RuleAction(r.result_action),
            targetCategory=r.target_category,
            priority=r.priority,
            enabled=r.enabled,
            createdAt=r.created_at,
        )
        for r in db_rules
    ]


@router.post(
    "",
    response_model=DynamicRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new dynamic rubric rule",
)
def create_rule(
    rule_in: DynamicRuleCreate,
    db: Session = Depends(get_db),
) -> DynamicRuleResponse:
    now = get_clock().now()
    new_rule = RiskRuleModel(
        rule_id=rule_in.ruleId,
        name=rule_in.name,
        conditions=rule_in.conditions,
        result_action=rule_in.resultAction.value,
        target_category=rule_in.targetCategory,
        priority=rule_in.priority,
        enabled=rule_in.enabled,
        created_at=now,
    )
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)

    return DynamicRuleResponse(
        id=new_rule.id,
        ruleId=new_rule.rule_id,
        name=new_rule.name,
        conditions=new_rule.conditions,
        resultAction=RuleAction(new_rule.result_action),
        targetCategory=new_rule.target_category,
        priority=new_rule.priority,
        enabled=new_rule.enabled,
        createdAt=new_rule.created_at,
    )
