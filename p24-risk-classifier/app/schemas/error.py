"""Standardized API Error Response Schema."""
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class ErrorResponse(BaseModel):
    """Consistent JSON error response."""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: int = Field(..., description="HTTP status code")
    error: str = Field(..., description="Machine-readable error classification code")
    message: str = Field(..., description="Human-readable description of the error")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional context or validation errors")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "timestamp": "2026-09-01T12:00:00Z",
                "status": 400,
                "error": "MISSING_OBLIGATIONS",
                "message": "Operation classified as Category 4 is missing required obligations: approval, rollbackPlan",
                "details": {
                    "riskCategory": 4,
                    "missingObligations": ["approval", "rollbackPlan"]
                }
            }
        }
    )
