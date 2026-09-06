"""Operation payload schemas.

IMPORTANT DESIGN RULE:
Obligation validation MUST NOT occur during initial schema validation.
This schema strictly validates the basic structural properties of an incoming operation.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict

from app.domain.enums import Scope, Reversibility, Persistence


class OperationPayload(BaseModel):
    """Structural schema for an operation subject to risk classification."""

    operationId: str = Field(..., description="Unique identifier for the operation", min_length=1)
    operationType: str = Field(..., description="Type of operation, e.g., DELETE, UPDATE, MIGRATE", min_length=1)
    scope: Scope = Field(..., description="Scope dimension: LOCAL, TEAM, ORGANIZATION, GLOBAL")
    reversibility: Reversibility = Field(..., description="Reversibility dimension: REVERSIBLE, PARTIALLY_REVERSIBLE, IRREVERSIBLE")
    persistence: Persistence = Field(..., description="Persistence dimension: TEMPORARY, LONG_TERM, PERMANENT")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Operation-specific metadata and parameters")
    timestamp: Optional[datetime] = Field(default=None, description="Timestamp of the operation request")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "operationId": "op-100",
                "operationType": "DELETE",
                "scope": "GLOBAL",
                "reversibility": "IRREVERSIBLE",
                "persistence": "PERMANENT",
                "payload": {
                    "environment": "PRODUCTION",
                    "resourceType": "DATABASE",
                    "recordCount": 100000
                }
            }
        }
    )
