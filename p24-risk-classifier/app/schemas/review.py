"""Schemas for two-engineer independent review scoring."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, AliasChoices

from app.domain.enums import ReviewStatus


class ReviewCreate(BaseModel):
    operationId: str = Field(..., description="Target operation ID", min_length=1)
    reviewerId: str = Field(..., description="Unique ID of the reviewer engineer", min_length=1)
    category: int = Field(..., ge=1, le=4, description="Independent risk category assessment (1-4)")
    reason: str = Field(..., description="Reviewer justification note", min_length=1)


class ReviewResponse(BaseModel):
    id: str
    operationId: str = Field(..., validation_alias=AliasChoices("operationId", "operation_id"))
    reviewerId: str = Field(..., validation_alias=AliasChoices("reviewerId", "reviewer_id"))
    category: int
    reason: str
    createdAt: datetime = Field(..., validation_alias=AliasChoices("createdAt", "created_at"))

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class DisagreementResponse(BaseModel):
    id: str
    operationId: str = Field(..., validation_alias=AliasChoices("operationId", "operation_id"))
    reviewerA: str = Field(..., validation_alias=AliasChoices("reviewerA", "reviewer_a"))
    categoryA: int = Field(..., validation_alias=AliasChoices("categoryA", "category_a"))
    reviewerB: str = Field(..., validation_alias=AliasChoices("reviewerB", "reviewer_b"))
    categoryB: int = Field(..., validation_alias=AliasChoices("categoryB", "category_b"))
    note: str
    createdAt: datetime = Field(..., validation_alias=AliasChoices("createdAt", "created_at"))

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ReviewSubmissionResult(BaseModel):
    """Result returned after submitting a review."""
    operationId: str
    review: ReviewResponse
    reviewStatus: ReviewStatus
    reviewCount: int
    agreementReached: bool
    disagreement: Optional[DisagreementResponse] = None
    message: str

    model_config = ConfigDict(populate_by_name=True)


class OperationReviewsResponse(BaseModel):
    operationId: str
    status: ReviewStatus
    reviews: List[ReviewResponse]
    disagreement: Optional[DisagreementResponse] = None

    model_config = ConfigDict(populate_by_name=True)
