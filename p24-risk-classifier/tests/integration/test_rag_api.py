"""Integration tests for RAG API endpoints and Web UI Dashboard."""
import pytest
from fastapi.testclient import TestClient


class TestRAGApi:
    def test_dashboard_html_endpoint(self, client: TestClient):
        res = client.get("/")
        assert res.status_code == 200
        assert "text/html" in res.headers["content-type"]
        assert "P24 Risk Classifier" in res.text
        assert "RAG" in res.text

    def test_rag_query_endpoint(self, client: TestClient):
        payload = {
            "query": "Production database delete snapshot backup",
            "topK": 3,
        }
        res = client.post("/api/v1/rag/query", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["retrievedCount"] > 0
        assert len(data["chunks"]) > 0
        assert "docId" in data["chunks"][0]

    def test_rag_list_and_add_documents(self, client: TestClient):
        # List
        res_list = client.get("/api/v1/rag/documents")
        assert res_list.status_code == 200
        docs = res_list.json()
        assert len(docs) >= 5

        # Add
        new_doc = {
            "docId": "POL-999",
            "title": "API Gateway Rate Limit Override SOP",
            "category": "Networking",
            "content": "Overriding API rate limits requires engineering lead confirmation.",
            "mandatoryObligations": ["approval"],
        }
        res_add = client.post("/api/v1/rag/documents", json=new_doc)
        assert res_add.status_code == 201
        assert res_add.json()["docId"] == "POL-999"

    def test_rag_evaluate_full_flow(self, client: TestClient):
        payload = {
            "operationId": "op-rag-demo",
            "operationType": "DELETE",
            "scope": "GLOBAL",
            "reversibility": "IRREVERSIBLE",
            "persistence": "PERMANENT",
            "payload": {
                "environment": "PRODUCTION",
                "approval": "CAB-2026-99",
                "justification": "Purge deprecated DB",
                "rollbackPlan": "Snapshot snapshot-rds-20260901",
            },
        }
        res = client.post("/api/v1/rag/evaluate", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert data["finalCategory"] == 4
        assert data["categoryLabel"] == "CRITICAL"
        assert data["obligationsSatisfied"] is True
        assert len(data["ragCitations"]) > 0
        assert "RAG Grounded Assessment:" in data["ragExecutiveSummary"]
