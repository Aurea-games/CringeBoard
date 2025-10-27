from fastapi import APIRouter

from . import delete, login, register

router = APIRouter(prefix="/v1/auth", tags=["auth"])
router.include_router(register.router)
router.include_router(login.router)
router.include_router(delete.router)

__all__ = ["router"]
