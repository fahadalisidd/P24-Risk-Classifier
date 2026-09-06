"""Two-Engineer Independent Scoring and Review Service."""
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateReviewException, ResourceNotFoundException
from app.domain.enums import ReviewStatus
from app.domain.models import ReviewModel, ReviewDisagreementModel
from app.schemas.review import (
    ReviewCreate,
    ReviewResponse,
    DisagreementResponse,
    ReviewSubmissionResult,
    OperationReviewsResponse,
)


class ReviewService:
    """Service handling independent engineer reviews, agreement detection, and disagreement notes."""

    def __init__(self, db: Session):
        self.db = db

    def submit_review(self, review_in: ReviewCreate) -> ReviewSubmissionResult:
        """Submit an independent review score for an operation."""
        # 1. Check if this reviewer already submitted for this operation
        existing_reviewer_review = (
            self.db.query(ReviewModel)
            .filter(
                ReviewModel.operation_id == review_in.operationId,
                ReviewModel.reviewer_id == review_in.reviewerId,
            )
            .first()
        )
        if existing_reviewer_review:
            raise DuplicateReviewException(
                operation_id=review_in.operationId,
                reviewer_id=review_in.reviewerId,
            )

        # 2. Save the new review
        new_review = ReviewModel(
            operation_id=review_in.operationId,
            reviewer_id=review_in.reviewerId,
            category=review_in.category,
            reason=review_in.reason,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(new_review)
        self.db.commit()
        self.db.refresh(new_review)

        # 3. Retrieve all reviews for this operation
        all_reviews = (
            self.db.query(ReviewModel)
            .filter(ReviewModel.operation_id == review_in.operationId)
            .order_by(ReviewModel.created_at.asc())
            .all()
        )

        review_count = len(all_reviews)
        disagreement_dto: Optional[DisagreementResponse] = None

        if review_count == 1:
            # First review submitted
            status = ReviewStatus.PENDING_SECOND_REVIEW
            agreement = False
            msg = f"Review by '{review_in.reviewerId}' recorded. Awaiting second independent review."
        elif review_count >= 2:
            first_review = all_reviews[0]
            second_review = all_reviews[1]

            if first_review.category == second_review.category:
                status = ReviewStatus.AGREEMENT
                agreement = True
                msg = f"Agreement reached: Both reviewers ({first_review.reviewer_id}, {second_review.reviewer_id}) agreed on Category {first_review.category}."
            else:
                status = ReviewStatus.DISAGREEMENT
                agreement = False
                note_text = (
                    f"Disagreement detected: {first_review.reviewer_id} assigned Category {first_review.category} "
                    f"('{first_review.reason}'), whereas {second_review.reviewer_id} assigned Category {second_review.category} "
                    f"('{second_review.reason}')."
                )

                # Check if disagreement already recorded
                existing_disagreement = (
                    self.db.query(ReviewDisagreementModel)
                    .filter(ReviewDisagreementModel.operation_id == review_in.operationId)
                    .first()
                )
                if not existing_disagreement:
                    disagreement_record = ReviewDisagreementModel(
                        operation_id=review_in.operationId,
                        reviewer_a=first_review.reviewer_id,
                        category_a=first_review.category,
                        reviewer_b=second_review.reviewer_id,
                        category_b=second_review.category,
                        note=note_text,
                        created_at=datetime.now(timezone.utc),
                    )
                    self.db.add(disagreement_record)
                    self.db.commit()
                    self.db.refresh(disagreement_record)
                    disagreement_dto = DisagreementResponse.model_validate(disagreement_record)
                else:
                    disagreement_dto = DisagreementResponse.model_validate(existing_disagreement)

                msg = f"Disagreement recorded between {first_review.reviewer_id} (Category {first_review.category}) and {second_review.reviewer_id} (Category {second_review.category})."
        else:
            status = ReviewStatus.PENDING_SECOND_REVIEW
            agreement = False
            msg = "Review recorded."

        return ReviewSubmissionResult(
            operationId=review_in.operationId,
            review=ReviewResponse.model_validate(new_review),
            reviewStatus=status,
            reviewCount=review_count,
            agreementReached=agreement,
            disagreement=disagreement_dto,
            message=msg,
        )

    def get_operation_reviews(self, operation_id: str) -> OperationReviewsResponse:
        """Get all reviews and agreement/disagreement status for an operation."""
        reviews = (
            self.db.query(ReviewModel)
            .filter(ReviewModel.operation_id == operation_id)
            .order_by(ReviewModel.created_at.asc())
            .all()
        )

        if not reviews:
            raise ResourceNotFoundException(resource_type="Reviews for operation", resource_id=operation_id)

        disagreement = (
            self.db.query(ReviewDisagreementModel)
            .filter(ReviewDisagreementModel.operation_id == operation_id)
            .first()
        )

        if len(reviews) == 1:
            status = ReviewStatus.PENDING_SECOND_REVIEW
        elif len(reviews) >= 2:
            if reviews[0].category == reviews[1].category:
                status = ReviewStatus.AGREEMENT
            else:
                status = ReviewStatus.DISAGREEMENT
        else:
            status = ReviewStatus.PENDING_SECOND_REVIEW

        return OperationReviewsResponse(
            operationId=operation_id,
            status=status,
            reviews=[ReviewResponse.model_validate(r) for r in reviews],
            disagreement=DisagreementResponse.model_validate(disagreement) if disagreement else None,
        )
