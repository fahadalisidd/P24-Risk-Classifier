"""RAG (Retrieval-Augmented Generation) API endpoints."""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.rag.rag_engine import RAGEngine
from app.rag.vector_store import rag_vector_store
from app.schemas.operation import OperationPayload
from app.schemas.rag import (
    RAGDocumentCreate,
    RAGDocumentResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    RAGRiskEvaluationResponse,
)
from app.service.risk_service import RiskClassificationService

router = APIRouter(prefix="/rag", tags=["RAG Policy & Incident Knowledge Base"])


@router.post(
    "/evaluate",
    response_model=RAGRiskEvaluationResponse,
    summary="RAG-Augmented Risk Classification",
    description=(
        "Executes deterministic risk classification, retrieves matching company policies and historical "
        "incident postmortems via semantic vector search, and produces grounded AI risk insights with citations."
    ),
)
def evaluate_with_rag(
    request: OperationPayload,
    db: Session = Depends(get_db),
) -> RAGRiskEvaluationResponse:
    risk_service = RiskClassificationService(db=db)
    rag_engine = RAGEngine()
    return rag_engine.evaluate_with_rag(operation=request, risk_service=risk_service)


@router.post(
    "/query",
    response_model=RAGQueryResponse,
    summary="Semantic Search Policy Knowledge Base",
    description="Searches indexed policy documents, runbooks, and incident postmortems using semantic vector similarity.",
)
def query_knowledge_base(
    query_in: RAGQueryRequest,
) -> RAGQueryResponse:
    rag_engine = RAGEngine()
    return rag_engine.query_knowledge_base(query=query_in.query, top_k=query_in.topK)


@router.get(
    "/documents",
    response_model=List[RAGDocumentResponse],
    summary="List all indexed RAG Policy Documents",
    description="Returns all policy runbooks and postmortems currently indexed in the vector store.",
)
def list_documents() -> List[RAGDocumentResponse]:
    return [
        RAGDocumentResponse(
            docId=doc.docId,
            title=doc.title,
            category=doc.category,
            content=doc.content,
            mandatoryObligations=doc.mandatoryObligations,
        )
        for doc in rag_vector_store.documents.values()
    ]


@router.post(
    "/documents",
    response_model=RAGDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Index new Policy or Runbook into Vector Store",
    description="Dynamically adds and indexes a new policy document or incident postmortem into the semantic vector store.",
)
def add_document(
    doc_in: RAGDocumentCreate,
) -> RAGDocumentResponse:
    rag_vector_store.add_document(doc_in)
    return RAGDocumentResponse(
        docId=doc_in.docId,
        title=doc_in.title,
        category=doc_in.category,
        content=doc_in.content,
        mandatoryObligations=doc_in.mandatoryObligations,
    )
