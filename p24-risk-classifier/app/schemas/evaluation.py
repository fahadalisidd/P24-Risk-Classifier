"""Schemas for risk evaluation requests and responses."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.operation import OperationPayload
from app.schemas.ai import AIRiskAssessment


class RiskEvaluationRequest(OperationPayload):
    """Evaluation request model extending structural OperationPayload."""
    pass


class RiskEvaluationResponse(BaseModel):
    """Explainable risk evaluation result."""

    operationId: str = Field(..., description="Unique operation identifier")
    riskScore: int = Field(..., description="Calculated static risk score (Scope × Reversibility × Persistence)")
    baseCategory: int = Field(..., description="Base category from static rubric (1-4)")
    rubricCategory: int = Field(..., description="Category after evaluating dynamic rubric rules (1-4)")
    finalCategory: int = Field(..., description="Final resolved risk category after overrides and pins (1-4)")

    matchedRules: List[str] = Field(default_factory=list, description="IDs of dynamic rules that matched")
    overrideApplied: bool = Field(default=False, description="Whether a policy override was applied")
    overrideCategory: Optional[int] = Field(default=None, description="Forced category from policy override if applied")
    overrideReason: Optional[str] = Field(default=None, description="Reason for policy override if applied")

    classificationReasons: List[str] = Field(default_factory=list, description="Step-by-step explainability notes")
    requiredObligations: List[str] = Field(default_factory=list, description="Obligations required for the final risk category")
    obligationsSatisfied: bool = Field(..., description="True if all required obligations are present in operation payload")
    missingObligations: List[str] = Field(default_factory=list, description="List of required obligations that were missing")

    aiAssessment: Optional[AIRiskAssessment] = Field(default=None, description="Optional AI Model Risk Advisor and Semantic Justification Analysis")

    evaluatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Evaluation timestamp")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "operationId": "op-123",
                "riskScore": 64,
                "baseCategory": 4,
                "rubricCategory": 4,
                "finalCategory": 4,
                "matchedRules": ["PRODUCTION_IRREVERSIBLE_DELETE"],
                "overrideApplied": False,
                "overrideCategory": None,
                "overrideReason": None,
                "classificationReasons": [
                    "Static Rubric: GLOBAL (4) × IRREVERSIBLE (4) × PERMANENT (4) = Score 64 -> Base Category 4",
                    "Dynamic Rule 'PRODUCTION_IRREVERSIBLE_DELETE' matched -> Set minimum category 4"
                ],
                "requiredObligations": ["approval", "justification", "rollbackPlan"],
                "obligationsSatisfied": False,
                "missingObligations": ["approval", "rollbackPlan"],
                "aiAssessment": {
                    "aiModelUsed": "Gemini 2.5 Flash / Semantic Risk Engine",
                    "aiConfidenceScore": 0.95,
                    "executiveSummary": "High-impact irreversible deletion in production targeting core database assets.",
                    "justificationQuality": "HIGH",
                    "rollbackPlanQuality": "STRONG",
                    "semanticRedFlags": [],
                    "suggestedMitigations": [
                        "Verify snapshot restore in staging prior to production execution"
                    ],
                    "recommendedCategory": 4
                },
                "evaluatedAt": "2026-09-01T12:00:00Z"
            }
        }
    )
