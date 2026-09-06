"""Unit tests for Grok and Ollama AI Risk Advisor."""
from unittest.mock import patch, MagicMock
import pytest

from app.ai.ai_advisor import AIRiskAdvisor
from app.domain.enums import Scope, Reversibility, Persistence
from app.schemas.operation import OperationPayload


class TestAIRiskAdvisor:
    @pytest.fixture
    def advisor(self):
        return AIRiskAdvisor(use_ollama=True, ollama_model="llama3.2")

    def test_ai_detects_insufficient_justification(self, advisor):
        op = OperationPayload(
            operationId="op-ai-1",
            operationType="DELETE",
            scope=Scope.GLOBAL,
            reversibility=Reversibility.IRREVERSIBLE,
            persistence=Persistence.PERMANENT,
            payload={"environment": "PRODUCTION", "justification": ""},
        )
        res = advisor.analyze(op, rule_category=4)
        assert res.justificationQuality == "INSUFFICIENT"
        assert res.rollbackPlanQuality == "MISSING"
        assert any("No justification was provided" in f for f in res.semanticRedFlags)
        assert res.recommendedCategory == 4

    def test_ai_evaluates_strong_justification_and_rollback(self, advisor):
        op = OperationPayload(
            operationId="op-ai-2",
            operationType="DELETE",
            scope=Scope.GLOBAL,
            reversibility=Reversibility.IRREVERSIBLE,
            persistence=Persistence.PERMANENT,
            payload={
                "environment": "PRODUCTION",
                "justification": "Planned decommissioning of deprecated Q3 analytics cluster with CAB signoff.",
                "rollbackPlan": "Full snapshot backup snap-2026-08-30 with point-in-time recovery enabled.",
            },
        )
        res = advisor.analyze(op, rule_category=4)
        assert res.justificationQuality == "HIGH"
        assert res.rollbackPlanQuality == "STRONG"
        assert len(res.suggestedMitigations) > 0

    @patch("httpx.Client.post")
    def test_grok_live_response_mock(self, mock_post):
        """Verify parsing when xAI Grok API key is provided."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '{"aiConfidenceScore": 0.99, "executiveSummary": "Grok 2 analyzed this critical DB deletion.", "justificationQuality": "HIGH", "rollbackPlanQuality": "STRONG", "semanticRedFlags": [], "suggestedMitigations": ["Check replication lag"], "recommendedCategory": 4}'
                    }
                }
            ]
        }
        mock_post.return_value = mock_resp

        grok_advisor = AIRiskAdvisor(grok_api_key="xai-test-key", grok_model="grok-2-latest")
        op = OperationPayload(
            operationId="op-grok-live",
            operationType="DELETE",
            scope=Scope.GLOBAL,
            reversibility=Reversibility.IRREVERSIBLE,
            persistence=Persistence.PERMANENT,
            payload={"environment": "PRODUCTION", "justification": "Emergency DB cleanup"},
        )
        res = grok_advisor.analyze(op, rule_category=4)
        assert res.aiModelUsed == "xAI Grok (grok-2-latest)"
        assert res.aiConfidenceScore == 0.99
        assert res.recommendedCategory == 4
        assert res.rollbackPlanQuality == "STRONG"

    @patch("httpx.Client.post")
    def test_ollama_live_response_mock(self, mock_post, advisor):
        """Verify parsing when Ollama HTTP service is live."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "response": '{"aiConfidenceScore": 0.98, "executiveSummary": "Llama 3.2 analyzed this critical DB deletion.", "justificationQuality": "HIGH", "rollbackPlanQuality": "STRONG", "semanticRedFlags": [], "suggestedMitigations": ["Check replica sync"], "recommendedCategory": 4}'
        }
        mock_post.return_value = mock_resp

        op = OperationPayload(
            operationId="op-ollama-live",
            operationType="DELETE",
            scope=Scope.GLOBAL,
            reversibility=Reversibility.IRREVERSIBLE,
            persistence=Persistence.PERMANENT,
            payload={"environment": "PRODUCTION", "justification": "Valid reason"},
        )
        res = advisor.analyze(op, rule_category=4)
        assert res.aiModelUsed == "Ollama (llama3.2)"
        assert res.aiConfidenceScore == 0.98
        assert res.recommendedCategory == 4
        assert res.rollbackPlanQuality == "STRONG"
