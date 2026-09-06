"""Risk classification evaluation API endpoint."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.evaluation import RiskEvaluationRequest, RiskEvaluationResponse
from app.service.risk_service import RiskClassificationService

router = APIRouter(prefix="/risk", tags=["Risk Classification"])


@router.post(
    "/evaluate",
    response_model=RiskEvaluationResponse,
    summary="Evaluate operation risk and obligations",
    description=(
        "Executes deterministic risk classification (Static rubric -> Dynamic rules -> "
        "Policy pins -> Policy overrides) and evaluates category obligations."
    ),
)
def evaluate_risk(
    request: RiskEvaluationRequest,
    db: Session = Depends(get_db),
) -> RiskEvaluationResponse:
    service = RiskClassificationService(db=db)
    return service.evaluate(request)
