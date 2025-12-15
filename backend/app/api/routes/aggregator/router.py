from fastapi import APIRouter

from . import articles, me, newspapers, public

router = APIRouter()
router.include_router(newspapers.router)
router.include_router(articles.router)
router.include_router(me.router)
router.include_router(public.router)

__all__ = ["router"]
