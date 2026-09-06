"""API v1 router configuration."""
from fastapi import APIRouter

from app.api.v1.endpoints.risk import router as risk_router
from app.api.v1.endpoints.reviews import router as reviews_router
from app.api.v1.endpoints.pins import router as pins_router
from app.api.v1.endpoints.overrides import router as overrides_router
from app.api.v1.endpoints.rules import router as rules_router
from app.api.v1.endpoints.ai import router as ai_router
from app.api.v1.endpoints.rag import router as rag_router

api_router = APIRouter()

api_router.include_router(risk_router)
api_router.include_router(reviews_router)
api_router.include_router(pins_router)
api_router.include_router(overrides_router)
api_router.include_router(rules_router)
api_router.include_router(ai_router)
api_router.include_router(rag_router)
