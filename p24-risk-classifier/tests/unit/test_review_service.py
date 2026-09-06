"""Unit tests for Two-Engineer Independent Review Service."""
import pytest
from app.core.exceptions import DuplicateReviewException, ResourceNotFoundException
from app.domain.enums import ReviewStatus
from app.review.review_service import ReviewService
from app.schemas.review import ReviewCreate


class TestReviewService:
    def test_single_review_submission(self, db_session):
        service = ReviewService(db=db_session)
        rev1 = ReviewCreate(
            operationId="op-test-1",
            reviewerId="engineer-alice",
            category=3,
            reason="High impact team migration",
        )
        res = service.submit_review(rev1)

        assert res.reviewCount == 1
        assert res.reviewStatus == ReviewStatus.PENDING_SECOND_REVIEW
        assert res.agreementReached is False
        assert res.disagreement is None

    def test_two_engineers_agreement(self, db_session):
        service = ReviewService(db=db_session)

        # Alice scores category 3
        service.submit_review(
            ReviewCreate(
                operationId="op-agree",
                reviewerId="engineer-alice",
                category=3,
                reason="Global scope, reversible",
            )
        )

        # Bob independently scores category 3
        res2 = service.submit_review(
            ReviewCreate(
                operationId="op-agree",
                reviewerId="engineer-bob",
                category=3,
                reason="Agreed on high impact",
            )
        )

        assert res2.reviewCount == 2
        assert res2.reviewStatus == ReviewStatus.AGREEMENT
        assert res2.agreementReached is True
        assert res2.disagreement is None

        # Verify all reviews are stored
        op_reviews = service.get_operation_reviews("op-agree")
        assert len(op_reviews.reviews) == 2
        assert op_reviews.reviews[0].reviewerId == "engineer-alice"
        assert op_reviews.reviews[1].reviewerId == "engineer-bob"

    def test_two_engineers_disagreement(self, db_session):
        service = ReviewService(db=db_session)

        # Alice scores category 3
        service.submit_review(
            ReviewCreate(
                operationId="op-disagree",
                reviewerId="engineer-alice",
                category=3,
                reason="Reversible data backfill",
            )
        )

        # Bob scores category 4
        res2 = service.submit_review(
            ReviewCreate(
                operationId="op-disagree",
                reviewerId="engineer-bob",
                category=4,
                reason="Touches critical production database without lock",
            )
        )

        assert res2.reviewCount == 2
        assert res2.reviewStatus == ReviewStatus.DISAGREEMENT
        assert res2.agreementReached is False
        assert res2.disagreement is not None
        assert res2.disagreement.reviewerA == "engineer-alice"
        assert res2.disagreement.categoryA == 3
        assert res2.disagreement.reviewerB == "engineer-bob"
        assert res2.disagreement.categoryB == 4
        assert "Disagreement detected" in res2.disagreement.note

        # Verify original reviews are never overwritten
        op_reviews = service.get_operation_reviews("op-disagree")
        assert len(op_reviews.reviews) == 2
        assert op_reviews.reviews[0].category == 3
        assert op_reviews.reviews[1].category == 4

    def test_duplicate_reviewer_rejected(self, db_session):
        service = ReviewService(db=db_session)
        service.submit_review(
            ReviewCreate(
                operationId="op-dup",
                reviewerId="engineer-alice",
                category=2,
                reason="Initial score",
            )
        )

        with pytest.raises(DuplicateReviewException):
            service.submit_review(
                ReviewCreate(
                    operationId="op-dup",
                    reviewerId="engineer-alice",
                    category=3,
                    reason="Updated score attempt",
                )
            )
