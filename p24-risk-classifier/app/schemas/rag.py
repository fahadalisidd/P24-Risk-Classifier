"""Schemas for RAG (Retrieval-Augmented Generation) Policy & Incident Knowledge Base."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.ai import AIRiskAssessment
from app.schemas.operation import OperationPayload


class RAGDocumentCreate(BaseModel):
    """Schema for adding a new policy or runbook document to the RAG vector store."""
    docId: str = Field(..., description="Unique document ID (e.g., POL-105, INC-2026-01)")
    title: str = Field(..., description="Document title")
    category: str = Field(..., description="Policy category (e.g., Security, Database, Compliance, Postmortem)")
    content: str = Field(..., description="Full text body of the policy document or incident runbook")
    mandatoryObligations: List[str] = Field(default_factory=list, description="Obligations enforced by this policy")


class RAGDocumentResponse(RAGDocumentCreate):
    """Schema for an indexed RAG document."""
    indexedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(populate_by_name=True)


class RAGRetrievedChunk(BaseModel):
    """A retrieved context chunk from vector search."""
    docId: str
    title: str
    category: str
    similarityScore: float = Field(..., description="Vector similarity matching score (0.0 to 1.0)")
    excerpt: str
    mandatoryObligations: List[str] = Field(default_factory=list)


class RAGQueryRequest(BaseModel):
    """Query request for semantic search in policy knowledge base."""
    query: str = Field(..., description="Search query or operation description", min_length=2)
    topK: int = Field(default=3, ge=1, le=10, description="Number of relevant documents to retrieve")


class RAGQueryResponse(BaseModel):
    """Response containing retrieved policy documents."""
    query: str
    retrievedCount: int
    chunks: List[RAGRetrievedChunk]


class RAGRiskEvaluationResponse(BaseModel):
    """Comprehensive RAG-Augmented Risk Classification Response."""
    operationId: str
    riskScore: int
    baseCategory: int
    finalCategory: int
    categoryLabel: str
    matchedRules: List[str]
    requiredObligations: List[str]
    obligationsSatisfied: bool
    missingObligations: List[str]
    classificationReasons: List[str]
    
    # RAG specific fields
    ragCitations: List[RAGRetrievedChunk] = Field(default_factory=list, description="Policy documents and incident precedents retrieved via vector search")
    ragExecutiveSummary: str = Field(..., description="Grounded risk analysis referencing specific company policies")
    aiAssessment: Optional[AIRiskAssessment] = None
    evaluatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(populate_by_name=True)
