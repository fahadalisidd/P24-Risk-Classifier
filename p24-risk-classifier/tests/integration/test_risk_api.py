"""Integration tests for Risk Evaluation API endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.enums import RuleAction
from app.domain.models import RiskRuleModel, RiskEvaluationModel


class TestRiskApi:
    def test_lowest_risk_evaluation_endpoint(self, client: TestClient, db_session: Session):
        payload = {
            "operationId": "op-low-1",
            "operationType": "READ",
            "scope": "LOCAL",
            "reversibility": "REVERSIBLE",
            "persistence": "TEMPORARY",
            "payload": {"environment": "DEV"},
        }
        response = client.post("/api/v1/risk/evaluate", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["operationId"] == "op-low-1"
        assert data["riskScore"] == 1
        assert data["baseCategory"] == 1
        assert data["finalCategory"] == 1
        assert data["requiredObligations"] == []
        assert data["obligationsSatisfied"] is True
        assert data["missingObligations"] == []

        # Verify DB persistence
        record = db_session.query(RiskEvaluationModel).filter_by(operation_id="op-low-1").first()
        assert record is not None
        assert record.final_category == 1

    def test_category_2_evaluation_endpoint(self, client: TestClient):
        payload = {
            "operationId": "op-med-1",
            "operationType": "UPDATE",
            "scope": "TEAM",
            "reversibility": "PARTIALLY_REVERSIBLE",
            "persistence": "LONG_TERM",
            "payload": {"justification": "Team dashboard refresh"},
        }
        # 2 * 2 * 2 = 8 -> Category 2 (MEDIUM)
        response = client.post("/api/v1/risk/evaluate", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["riskScore"] == 8
        assert data["baseCategory"] == 2
        assert data["finalCategory"] == 2
        assert data["requiredObligations"] == ["justification"]
        assert data["obligationsSatisfied"] is True

    def test_category_4_with_missing_obligations_endpoint(self, client: TestClient):
        payload = {
            "operationId": "op-crit-missing",
            "operationType": "DELETE",
            "scope": "GLOBAL",
            "reversibility": "IRREVERSIBLE",
            "persistence": "PERMANENT",
            "payload": {
                "environment": "PRODUCTION",
                # missing approval, justification, rollbackPlan
            },
        }
        response = client.post("/api/v1/risk/evaluate", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["riskScore"] == 64
        assert data["finalCategory"] == 4
        assert set(data["requiredObligations"]) == {"approval", "justification", "rollbackPlan"}
        assert data["obligationsSatisfied"] is False
        assert set(data["missingObligations"]) == {"approval", "justification", "rollbackPlan"}

    def test_category_4_with_satisfied_obligations_endpoint(self, client: TestClient):
        payload = {
            "operationId": "op-crit-satisfied",
            "operationType": "DELETE",
            "scope": "GLOBAL",
            "reversibility": "IRREVERSIBLE",
            "persistence": "PERMANENT",
            "payload": {
                "environment": "PRODUCTION",
                "approval": "CAB-2026-9901",
                "justification": "Annual DB pruning",
                "rollbackPlan": "Full snapshot RDS-2026-08-31",
            },
        }
        response = client.post("/api/v1/risk/evaluate", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["finalCategory"] == 4
        assert data["obligationsSatisfied"] is True
        assert data["missingObligations"] == []

    def test_invalid_enum_validation_error(self, client: TestClient):
        payload = {
            "operationId": "op-bad-enum",
            "operationType": "READ",
            "scope": "INVALID_SCOPE_NAME",
            "reversibility": "REVERSIBLE",
            "persistence": "TEMPORARY",
            "payload": {},
        }
        response = client.post("/api/v1/risk/evaluate", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "VALIDATION_ERROR"
