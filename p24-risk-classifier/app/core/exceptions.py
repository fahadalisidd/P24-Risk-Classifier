"""Application and domain exceptions."""
from typing import Any, Dict, Optional


class AppException(Exception):
    """Base exception for application errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "APPLICATION_ERROR",
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}


class InvalidOperationException(AppException):
    """Raised when an operation payload structure or data is invalid."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="INVALID_OPERATION",
            status_code=400,
            details=details,
        )


class UnknownEnumValueException(AppException):
    """Raised when an unrecognized enum or category value is supplied."""

    def __init__(self, field_name: str, value: Any):
        super().__init__(
            message=f"Unknown value '{value}' for enum field '{field_name}'",
            error_code="UNKNOWN_ENUM_VALUE",
            status_code=400,
            details={"field": field_name, "value": str(value)},
        )


class MissingObligationException(AppException):
    """Raised when required obligations are missing after classification."""

    def __init__(self, missing_obligations: list[str], risk_category: int):
        super().__init__(
            message=f"Operation classified as Category {risk_category} is missing required obligations: {', '.join(missing_obligations)}",
            error_code="MISSING_OBLIGATIONS",
            status_code=400,
            details={"riskCategory": risk_category, "missingObligations": missing_obligations},
        )


class ExpiredPolicyException(AppException):
    """Raised when an operation references an expired policy or pin."""

    def __init__(self, policy_id: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Policy '{policy_id}' has expired.",
            error_code="EXPIRED_POLICY",
            status_code=400,
            details={"policyId": policy_id},
        )


class InvalidPolicyPinException(AppException):
    """Raised when a policy pin is invalid or disabled."""

    def __init__(self, pin_id: str, reason: str):
        super().__init__(
            message=f"Policy pin '{pin_id}' is invalid: {reason}",
            error_code="INVALID_POLICY_PIN",
            status_code=400,
            details={"pinId": pin_id, "reason": reason},
        )


class DuplicateReviewException(AppException):
    """Raised when a reviewer submits multiple reviews for the same operation."""

    def __init__(self, operation_id: str, reviewer_id: str):
        super().__init__(
            message=f"Reviewer '{reviewer_id}' has already submitted a review for operation '{operation_id}'",
            error_code="DUPLICATE_REVIEW",
            status_code=409,
            details={"operationId": operation_id, "reviewerId": reviewer_id},
        )


class ResourceNotFoundException(AppException):
    """Raised when a requested entity does not exist."""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} with ID '{resource_id}' was not found.",
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={"resourceType": resource_type, "resourceId": resource_id},
        )
