"""SQLAlchemy ORM models for P24 Risk Rubric and Classifier."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    JSON,
    UniqueConstraint,
    Index,
)
from app.db.base import Base
from app.domain.enums import (
    Scope,
    Reversibility,
    Persistence,
    RiskCategory,
    RuleAction,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RiskRuleModel(Base):
    """Dynamic risk rubric rules."""
    __tablename__ = "risk_rules"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    conditions = Column(JSON, nullable=False, default=dict)
    result_action = Column(String(32), nullable=False, default=RuleAction.SET_MIN_CATEGORY.value)
    target_category = Column(Integer, nullable=False)
    priority = Column(Integer, nullable=False, default=100)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class PolicyOverrideModel(Base):
    """Explicit policy overrides forcing a risk category."""
    __tablename__ = "policy_overrides"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    conditions = Column(JSON, nullable=False, default=dict)
    forced_category = Column(Integer, nullable=False)
    reason = Column(Text, nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    expires_at = Column(DateTime(timezone=True), nullable=True)


class PolicyPinModel(Base):
    """Temporary policy pins with separate review and expiry dates."""
    __tablename__ = "policy_pins"

    pin_id = Column(String(64), primary_key=True)
    policy_id = Column(String(64), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    review_date = Column(DateTime(timezone=True), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    enabled = Column(Boolean, nullable=False, default=True)


class RiskEvaluationModel(Base):
    """Audit log of complete risk evaluation decisions."""
    __tablename__ = "risk_evaluations"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    operation_id = Column(String(128), nullable=False, index=True)
    operation_type = Column(String(64), nullable=False)
    scope = Column(String(32), nullable=False)
    reversibility = Column(String(32), nullable=False)
    persistence = Column(String(32), nullable=False)
    payload = Column(JSON, nullable=False, default=dict)

    risk_score = Column(Integer, nullable=False)
    base_category = Column(Integer, nullable=False)
    rubric_category = Column(Integer, nullable=False)
    final_category = Column(Integer, nullable=False)

    matched_rules = Column(JSON, nullable=False, default=list)
    override_applied = Column(Boolean, nullable=False, default=False)
    override_category = Column(Integer, nullable=True)
    override_reason = Column(Text, nullable=True)

    classification_reasons = Column(JSON, nullable=False, default=list)
    required_obligations = Column(JSON, nullable=False, default=list)
    obligations_satisfied = Column(Boolean, nullable=False, default=True)
    missing_obligations = Column(JSON, nullable=False, default=list)

    evaluated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class ReviewModel(Base):
    """Independent engineer reviews."""
    __tablename__ = "reviews"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    operation_id = Column(String(128), nullable=False, index=True)
    reviewer_id = Column(String(128), nullable=False, index=True)
    category = Column(Integer, nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        UniqueConstraint("operation_id", "reviewer_id", name="uq_operation_reviewer"),
    )


class ReviewDisagreementModel(Base):
    """Disagreement notes when independent reviewers assign different categories."""
    __tablename__ = "review_disagreements"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    operation_id = Column(String(128), nullable=False, index=True)
    reviewer_a = Column(String(128), nullable=False)
    category_a = Column(Integer, nullable=False)
    reviewer_b = Column(String(128), nullable=False)
    category_b = Column(Integer, nullable=False)
    note = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
