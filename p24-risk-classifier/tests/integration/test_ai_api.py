"""Integration tests for AI Risk Advisor API endpoints."""
import pytest
from fastapi.testclient import TestClient


class TestAIApi:
    def test_ai_analyze_endpoint(self, client: TestClient):
        payload = {
            "operationId": "op-ai-endpoint",
            "operationType": "DELETE",
            "scope": "GLOBAL",
            "reversibility": "IRREVERSIBLE",
            "persistence": "PERMANENT",
            "payload": {
                "environment": "PRODUCTION",
                "justification": "Emergency purge of corrupted user session cache",
                "rollbackPlan": "Restore from automated snapshot snapshot-rds-20260901",
            },
        }
        res = client.post("/api/v1/ai/analyze", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert "aiModelUsed" in data
        assert data["aiConfidenceScore"] > 0
        assert data["justificationQuality"] == "HIGH"
        assert data["rollbackPlanQuality"] == "STRONG"
        assert len(data["suggestedMitigations"]) > 0
        assert data["recommendedCategory"] == 4

    def test_risk_evaluate_includes_ai_assessment(self, client: TestClient):
        payload = {
            "operationId": "op-eval-ai",
            "operationType": "DELETE",
            "scope": "GLOBAL",
            "reversibility": "IRREVERSIBLE",
            "persistence": "PERMANENT",
            "payload": {
                "environment": "PRODUCTION",
                "approval": "CAB-2026-99",
                "justification": "Purge legacy logs",
                "rollbackPlan": "Snapshot available",
            },
        }
        res = client.post("/api/v1/risk/evaluate", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert "aiAssessment" in data
        assert data["aiAssessment"] is not None
        assert "aiModelUsed" in data["aiAssessment"]
        assert data["aiAssessment"]["recommendedCategory"] == 4
