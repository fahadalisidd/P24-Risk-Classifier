"""Schemas for dynamic rules, policy overrides, and policy pins."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict, AliasChoices

from app.domain.enums import PinStatus, RuleAction


# --- Dynamic Rules ---

class DynamicRuleCreate(BaseModel):
    ruleId: str = Field(..., validation_alias=AliasChoices("ruleId", "rule_id"), description="Unique business identifier for the rule")
    name: str = Field(..., description="Descriptive name")
    conditions: Dict[str, Any] = Field(..., description="Conditions to match against operation and payload")
    resultAction: RuleAction = Field(default=RuleAction.SET_MIN_CATEGORY, validation_alias=AliasChoices("resultAction", "result_action"), description="Action to take")
    targetCategory: int = Field(..., ge=1, le=4, validation_alias=AliasChoices("targetCategory", "target_category"), description="Target category (1-4)")
    priority: int = Field(default=100, description="Priority (higher number = evaluated/applied first)")
    enabled: bool = Field(default=True, description="Whether rule is active")

    model_config = ConfigDict(populate_by_name=True)


class DynamicRuleResponse(DynamicRuleCreate):
    id: str
    createdAt: datetime = Field(..., validation_alias=AliasChoices("createdAt", "created_at"))

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# --- Policy Overrides ---

class PolicyOverrideCreate(BaseModel):
    name: str = Field(..., description="Override name")
    conditions: Dict[str, Any] = Field(..., description="Match conditions")
    forcedCategory: int = Field(..., ge=1, le=4, validation_alias=AliasChoices("forcedCategory", "forced_category"), description="Forced category (1-4)")
    reason: str = Field(..., description="Mandatory reason for override", min_length=1)
    enabled: bool = Field(default=True, description="Whether override is active")
    expiresAt: Optional[datetime] = Field(default=None, validation_alias=AliasChoices("expiresAt", "expires_at"), description="Optional expiry timestamp")

    model_config = ConfigDict(populate_by_name=True)


class PolicyOverrideResponse(PolicyOverrideCreate):
    id: str
    createdAt: datetime = Field(..., validation_alias=AliasChoices("createdAt", "created_at"))

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# --- Policy Pins ---

class PolicyPinCreate(BaseModel):
    pinId: str = Field(..., validation_alias=AliasChoices("pinId", "pin_id"), description="Unique pin ID, e.g., pin-123")
    policyId: str = Field(..., validation_alias=AliasChoices("policyId", "policy_id"), description="Target policy identifier")
    reason: str = Field(..., description="Reason for pinning policy", min_length=1)
    reviewDate: datetime = Field(..., validation_alias=AliasChoices("reviewDate", "review_date"), description="Date by which pin must be reviewed")
    expiresAt: datetime = Field(..., validation_alias=AliasChoices("expiresAt", "expires_at"), description="Date when pin expires completely")
    enabled: bool = Field(default=True, description="Whether pin is active")

    model_config = ConfigDict(populate_by_name=True)


class PolicyPinResponse(PolicyPinCreate):
    createdAt: datetime = Field(..., validation_alias=AliasChoices("createdAt", "created_at"))
    status: PinStatus

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class PinReviewReportItem(BaseModel):
    """Entry in the pin review report."""
    pinId: str = Field(..., validation_alias=AliasChoices("pinId", "pin_id"))
    policyId: str = Field(..., validation_alias=AliasChoices("policyId", "policy_id"))
    reviewDate: datetime = Field(..., validation_alias=AliasChoices("reviewDate", "review_date"))
    expiresAt: datetime = Field(..., validation_alias=AliasChoices("expiresAt", "expires_at"))
    status: PinStatus
    daysOverdue: int = Field(..., description="Number of days past review date")
    reason: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class PinReviewReportResponse(BaseModel):
    """Response containing pins past review date."""
    reportGeneratedAt: datetime
    overduePinCount: int
    expiredReviewPins: List[PinReviewReportItem]

    model_config = ConfigDict(populate_by_name=True)
