from fastapi import APIRouter

from app.api.routes import aggregator, auth, system

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(aggregator.router)

__all__ = ["api_router"]
