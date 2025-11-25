from fastapi import APIRouter

from . import delete, login, refresh, register, profile

router = APIRouter(prefix="/v1/auth", tags=["auth"])
router.include_router(register.router)
router.include_router(login.router)
router.include_router(refresh.router)
router.include_router(delete.router)
router.include_router(profile.router)

__all__ = ["router"]
