"""AI Model Risk Advisor API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai.ai_advisor import AIRiskAdvisor
from app.db.session import get_db
from app.schemas.ai import AIAnalysisRequest, AIRiskAssessment
from app.service.risk_service import RiskClassificationService

router = APIRouter(prefix="/ai", tags=["AI Model Risk Advisor"])


@router.post(
    "/analyze",
    response_model=AIRiskAssessment,
    summary="AI Model Semantic Risk Analysis",
    description=(
        "Uses an AI Model (Gemini / OpenAI / Semantic NLP Engine) to evaluate free-text justifications, "
        "detect hidden operational red flags, grade rollback plans, and provide actionable mitigations."
    ),
)
def analyze_with_ai(
    request: AIAnalysisRequest,
    db: Session = Depends(get_db),
) -> AIRiskAssessment:
    advisor = AIRiskAdvisor()
    # Calculate rule category first to pass to AI as context
    service = RiskClassificationService(db=db)
    res = service.evaluate(request, include_ai=False)
    return advisor.analyze(request, rule_category=res.finalCategory)
