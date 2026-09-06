"""Schemas for AI Risk Advisor and Semantic Justification Analyzer."""
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.operation import OperationPayload


class AIRiskAssessment(BaseModel):
    """AI Model Risk Assessment and Semantic Analysis."""

    aiModelUsed: str = Field(..., description="Name of the AI Model used for evaluation")
    aiConfidenceScore: float = Field(..., description="AI confidence rating (0.0 - 1.0)")
    executiveSummary: str = Field(..., description="AI-generated plain English summary of operational risk")
    justificationQuality: str = Field(..., description="Quality of provided justification: HIGH, MEDIUM, LOW, INSUFFICIENT")
    rollbackPlanQuality: str = Field(..., description="Quality of provided rollback plan: STRONG, ADEQUATE, WEAK, MISSING")
    semanticRedFlags: List[str] = Field(default_factory=list, description="AI-detected semantic risks or safety gaps in text")
    suggestedMitigations: List[str] = Field(default_factory=list, description="Actionable AI safety advice")
    recommendedCategory: int = Field(..., ge=1, le=4, description="AI recommended risk category (1-4)")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "aiModelUsed": "Gemini 2.5 Flash / Semantic Risk Engine",
                "aiConfidenceScore": 0.95,
                "executiveSummary": "High-impact irreversible deletion in production targeting core database assets.",
                "justificationQuality": "HIGH",
                "rollbackPlanQuality": "STRONG",
                "semanticRedFlags": [
                    "Permanent persistence eliminates recovery after snapshot expiration"
                ],
                "suggestedMitigations": [
                    "Verify snapshot restore in staging prior to production execution",
                    "Conduct dry-run during off-peak maintenance window"
                ],
                "recommendedCategory": 4
            }
        }
    )


class AIAnalysisRequest(OperationPayload):
    """Request model for AI Risk Analysis."""
    pass
