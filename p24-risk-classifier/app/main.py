"""Main FastAPI Application entrypoint for P24 Risk Rubric and Classifier."""
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.domain.enums import RuleAction
from app.domain.models import RiskRuleModel, PolicyPinModel, PolicyOverrideModel


def seed_defaults() -> None:
    """Seed sample dynamic rules, overrides, and pins if database is empty."""
    db = SessionLocal()
    try:
        # 1. Seed Dynamic Rules if none exist
        if db.query(RiskRuleModel).count() == 0:
            now = datetime.now(timezone.utc)
            rule1 = RiskRuleModel(
                rule_id="PRODUCTION_IRREVERSIBLE_DELETE",
                name="Irreversible Delete in Production Database",
                conditions={
                    "operationType": "DELETE",
                    "payload.environment": "PRODUCTION",
                    "reversibility": "IRREVERSIBLE",
                },
                result_action=RuleAction.SET_MIN_CATEGORY.value,
                target_category=4,
                priority=200,
                enabled=True,
                created_at=now,
            )
            rule2 = RiskRuleModel(
                rule_id="GLOBAL_PERMANENT_DATABASE",
                name="Global Permanent Database Modification",
                conditions={
                    "payload.resourceType": "DATABASE",
                    "scope": "GLOBAL",
                    "persistence": "PERMANENT",
                },
                result_action=RuleAction.SET_MIN_CATEGORY.value,
                target_category=4,
                priority=150,
                enabled=True,
                created_at=now,
            )
            rule3 = RiskRuleModel(
                rule_id="HIGH_RECORD_COUNT_DELETE",
                name="Delete with > 50,000 records",
                conditions={
                    "operationType": "DELETE",
                    "payload.recordCount": {"gte": 50000},
                },
                result_action=RuleAction.SET_MIN_CATEGORY.value,
                target_category=3,
                priority=100,
                enabled=True,
                created_at=now,
            )
            db.add_all([rule1, rule2, rule3])
            db.commit()

        # 2. Seed Default Policy Pin for Demo/Testing if none exist
        if db.query(PolicyPinModel).count() == 0:
            from datetime import timedelta
            now = datetime.now(timezone.utc)
            pin1 = PolicyPinModel(
                pin_id="pin-prod-freeze-2026",
                policy_id="STRICT_CRITICAL_FREEZE",
                reason="Year-end change freeze policy pin requiring critical category escalation",
                created_at=now - timedelta(days=30),
                review_date=now - timedelta(days=10),  # Past review date -> REVIEW_OVERDUE
                expires_at=now + timedelta(days=30),   # Still active/usable
                enabled=True,
            )
            pin2 = PolicyPinModel(
                pin_id="pin-standard-ops",
                policy_id="STANDARD_POLICY",
                reason="Standard operations policy pin with future review date",
                created_at=now - timedelta(days=5),
                review_date=now + timedelta(days=25),  # Future review date -> ACTIVE
                expires_at=now + timedelta(days=60),
                enabled=True,
            )
            db.add_all([pin1, pin2])
            db.commit()

    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and shutdown hooks."""
    # Create DB tables
    Base.metadata.create_all(bind=engine)
    # Seed default data
    seed_defaults()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Production-quality deterministic risk classification engine implementing "
        "Scope × Reversibility × Persistence, dynamic payload rules, policy overrides, "
        "expiring policy-pin registry with review-date reporting, two-engineer independent "
        "review scoring, RAG Knowledge Base, and post-classification obligation evaluation."
    ),
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Centralized Exception Handlers
@app.exception_handler(AppException)
async def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": exc.status_code,
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    formatted_errors = []
    for err in exc.errors():
        field = " -> ".join([str(loc) for loc in err["loc"] if loc != "body"])
        formatted_errors.append(f"{field}: {err['msg']}")

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": 400,
            "error": "VALIDATION_ERROR",
            "message": f"Invalid request schema: {'; '.join(formatted_errors)}",
            "details": {"validation_errors": exc.errors()},
        },
    )


@app.exception_handler(Exception)
async def handle_generic_exception(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": 500,
            "error": "INTERNAL_SERVER_ERROR",
            "message": str(exc) if settings.DEBUG else "An unexpected internal server error occurred.",
            "details": {},
        },
    )


# Web UI Dashboard Routes
@app.get("/", response_class=HTMLResponse, tags=["Web Dashboard UI"])
@app.get("/dashboard", response_class=HTMLResponse, tags=["Web Dashboard UI"])
def get_dashboard():
    """Serve the interactive web frontend UI."""
    template_path = Path(__file__).parent / "templates" / "index.html"
    if template_path.exists():
        return HTMLResponse(content=template_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>P24 Risk Classifier API is Running.</h1><p>Visit <a href='/docs'>/docs</a> for Swagger UI.</p>")


# Health endpoint
@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# Include v1 API routes
app.include_router(api_router, prefix=settings.API_V1_STR)
