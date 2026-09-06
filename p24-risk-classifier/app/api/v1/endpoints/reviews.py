"""Reviewer independent scoring and disagreement detection endpoints."""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.review import (
    ReviewCreate,
    ReviewResponse,
    ReviewSubmissionResult,
    OperationReviewsResponse,
)
from app.review.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["Reviews & Disagreements"])


@router.post(
    "",
    response_model=ReviewSubmissionResult,
    status_code=status.HTTP_201_CREATED,
    summary="Submit independent engineer review",
    description=(
        "Submits an engineer's independent category assessment. If two reviews exist for the operation, "
        "detects agreement or automatically records a disagreement note."
    ),
)
def submit_review(
    review_in: ReviewCreate,
    db: Session = Depends(get_db),
) -> ReviewSubmissionResult:
    service = ReviewService(db=db)
    return service.submit_review(review_in)


@router.get(
    "/{operation_id}",
    response_model=OperationReviewsResponse,
    summary="Get reviews and consensus status for an operation",
)
def get_operation_reviews(
    operation_id: str,
    db: Session = Depends(get_db),
) -> OperationReviewsResponse:
    service = ReviewService(db=db)
    return service.get_operation_reviews(operation_id)
