"""Integration tests for Two-Engineer Reviews API endpoints."""
import pytest
from fastapi.testclient import TestClient


class TestReviewApi:
    def test_two_engineer_agreement_api_flow(self, client: TestClient):
        # 1. First review by engineer 1
        res1 = client.post(
            "/api/v1/reviews",
            json={
                "operationId": "op-api-agree",
                "reviewerId": "engineer-1",
                "category": 3,
                "reason": "Global rollout with partial rollback",
            },
        )
        assert res1.status_code == 201
        data1 = res1.json()
        assert data1["reviewStatus"] == "PENDING_SECOND_REVIEW"
        assert data1["agreementReached"] is False

        # 2. Second independent review by engineer 2 (same category)
        res2 = client.post(
            "/api/v1/reviews",
            json={
                "operationId": "op-api-agree",
                "reviewerId": "engineer-2",
                "category": 3,
                "reason": "Agreed, impact is high",
            },
        )
        assert res2.status_code == 201
        data2 = res2.json()
        assert data2["reviewStatus"] == "AGREEMENT"
        assert data2["agreementReached"] is True
        assert data2["disagreement"] is None

        # 3. GET reviews for operation
        get_res = client.get("/api/v1/reviews/op-api-agree")
        assert get_res.status_code == 200
        get_data = get_res.json()
        assert len(get_data["reviews"]) == 2
        assert get_data["status"] == "AGREEMENT"

    def test_two_engineer_disagreement_api_flow(self, client: TestClient):
        # 1. Reviewer 1 scores 2
        client.post(
            "/api/v1/reviews",
            json={
                "operationId": "op-api-disagree",
                "reviewerId": "engineer-1",
                "category": 2,
                "reason": "Reversible staging test",
            },
        )

        # 2. Reviewer 2 scores 4
        res2 = client.post(
            "/api/v1/reviews",
            json={
                "operationId": "op-api-disagree",
                "reviewerId": "engineer-2",
                "category": 4,
                "reason": "Direct production database connection detected",
            },
        )
        assert res2.status_code == 201
        data2 = res2.json()
        assert data2["reviewStatus"] == "DISAGREEMENT"
        assert data2["agreementReached"] is False
        assert data2["disagreement"] is not None
        assert data2["disagreement"]["categoryA"] == 2
        assert data2["disagreement"]["categoryB"] == 4

        # 3. GET reviews returns disagreement details
        get_res = client.get("/api/v1/reviews/op-api-disagree")
        assert get_res.status_code == 200
        get_data = get_res.json()
        assert get_data["status"] == "DISAGREEMENT"
        assert get_data["disagreement"] is not None

    def test_duplicate_review_submission_rejected(self, client: TestClient):
        client.post(
            "/api/v1/reviews",
            json={
                "operationId": "op-dup-api",
                "reviewerId": "engineer-1",
                "category": 2,
                "reason": "First attempt",
            },
        )
        # Duplicate submission by same engineer
        res_dup = client.post(
            "/api/v1/reviews",
            json={
                "operationId": "op-dup-api",
                "reviewerId": "engineer-1",
                "category": 3,
                "reason": "Second attempt",
            },
        )
        assert res_dup.status_code == 409
        assert res_dup.json()["error"] == "DUPLICATE_REVIEW"
