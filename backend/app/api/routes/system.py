from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["system"])


@router.get("/")
def read_root():
    settings = get_settings()
    return {"name": settings.project_name, "status": "ok"}


@router.get("/healthz")
def healthz():
    return {"status": "healthyyyy"}


__all__ = ["router"]

