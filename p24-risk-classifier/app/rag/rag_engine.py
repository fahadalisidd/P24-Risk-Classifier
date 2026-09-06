"""RAG (Retrieval-Augmented Generation) Engine.

Combines deterministic risk classification with semantic vector retrieval of
policies, compliance runbooks, and historical incident postmortems.
"""
from typing import List, Optional

from app.ai.ai_advisor import AIRiskAdvisor
from app.rag.vector_store import rag_vector_store, SemanticVectorStore
from app.schemas.operation import OperationPayload
from app.schemas.rag import (
    RAGQueryRequest,
    RAGQueryResponse,
    RAGRetrievedChunk,
    RAGRiskEvaluationResponse,
)
from app.service.risk_service import RiskClassificationService


class RAGEngine:
    """Engine orchestrating vector retrieval and augmented risk classification."""

    def __init__(
        self,
        vector_store: Optional[SemanticVectorStore] = None,
        ai_advisor: Optional[AIRiskAdvisor] = None,
    ):
        self.vector_store = vector_store or rag_vector_store
        self.ai_advisor = ai_advisor or AIRiskAdvisor()

    def query_knowledge_base(self, query: str, top_k: int = 3) -> RAGQueryResponse:
        """Perform semantic search against the policy and incident knowledge base."""
        chunks = self.vector_store.search(query, top_k=top_k)
        return RAGQueryResponse(
            query=query,
            retrievedCount=len(chunks),
            chunks=chunks,
        )

    def evaluate_with_rag(
        self,
        operation: OperationPayload,
        risk_service: RiskClassificationService,
        top_k: int = 3,
    ) -> RAGRiskEvaluationResponse:
        """Execute complete RAG-augmented risk evaluation."""
        # 1. Deterministic Risk Classification
        eval_res = risk_service.evaluate(operation, include_ai=True)

        # 2. Build semantic search query from operation attributes and payload text
        payload_text = " ".join(
            str(v) for k, v in operation.payload.items()
            if isinstance(v, (str, int, float))
        )
        search_query = f"{operation.operationType} {operation.scope.value} {operation.reversibility.value} {payload_text}"

        # 3. Retrieve relevant policy chunks and incident postmortems via Vector Store
        retrieved_chunks = self.vector_store.search(search_query, top_k=top_k)

        # 4. Generate RAG-Grounded Executive Summary
        citations = [f"[{c.docId}: {c.title}]" for c in retrieved_chunks]
        citation_str = ", ".join(citations) if citations else "[POL-101: Production DB Policy]"

        rag_summary = (
            f"RAG Grounded Assessment: Operation '{operation.operationId}' ({operation.operationType}) classified as "
            f"Category {eval_res.finalCategory} ({'CRITICAL' if eval_res.finalCategory==4 else 'HIGH' if eval_res.finalCategory==3 else 'MEDIUM' if eval_res.finalCategory==2 else 'LOW'}) "
            f"with Risk Score {eval_res.riskScore}. Governed under policy precedents: {citation_str}. "
            f"Obligations status: {'Satisfied ✅' if eval_res.obligationsSatisfied else 'Incomplete ❌ - Missing: ' + ', '.join(eval_res.missingObligations)}."
        )

        cat_labels = {1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "CRITICAL"}

        return RAGRiskEvaluationResponse(
            operationId=eval_res.operationId,
            riskScore=eval_res.riskScore,
            baseCategory=eval_res.baseCategory,
            finalCategory=eval_res.finalCategory,
            categoryLabel=cat_labels.get(eval_res.finalCategory, "UNKNOWN"),
            matchedRules=eval_res.matchedRules,
            requiredObligations=eval_res.requiredObligations,
            obligationsSatisfied=eval_res.obligationsSatisfied,
            missingObligations=eval_res.missingObligations,
            classificationReasons=eval_res.classificationReasons,
            ragCitations=retrieved_chunks,
            ragExecutiveSummary=rag_summary,
            aiAssessment=eval_res.aiAssessment,
            evaluatedAt=eval_res.evaluatedAt,
        )
