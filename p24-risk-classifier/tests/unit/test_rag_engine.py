"""Unit tests for RAG Semantic Vector Store and RAG Engine."""
import pytest
from app.rag.vector_store import SemanticVectorStore
from app.schemas.rag import RAGDocumentCreate


class TestRAGVectorStore:
    @pytest.fixture
    def store(self):
        return SemanticVectorStore()

    def test_default_seeded_documents(self, store):
        assert len(store.documents) >= 5
        assert "POL-101" in store.documents
        assert "POL-102" in store.documents

    def test_semantic_search_database_deletion(self, store):
        query = "DELETE production postgresql database without snapshot"
        results = store.search(query, top_k=3)
        assert len(results) > 0
        # POL-101 (Database Deletion) should be the top match
        assert results[0].docId in ("POL-101", "INC-2025-08")
        assert results[0].similarityScore >= 0.60
        assert "approval" in results[0].mandatoryObligations

    def test_semantic_search_emergency_override(self, store):
        query = "Emergency policy override bypass review date"
        results = store.search(query, top_k=3)
        assert len(results) > 0
        assert any(r.docId == "POL-102" for r in results)

    def test_add_custom_document(self, store):
        new_doc = RAGDocumentCreate(
            docId="POL-200",
            title="Kubernetes Cluster Hard Reset Runbook",
            category="Kubernetes",
            content="Hard resetting a production k8s control plane requires cluster drainage and etcd snapshot verification.",
            mandatoryObligations=["approval", "rollbackPlan"],
        )
        store.add_document(new_doc)
        assert "POL-200" in store.documents

        results = store.search("etcd control plane reset", top_k=2)
        assert any(r.docId == "POL-200" for r in results)
