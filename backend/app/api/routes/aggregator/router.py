from fastapi import APIRouter

from . import articles, me, newspapers

router = APIRouter()
router.include_router(newspapers.router)
router.include_router(articles.router)
router.include_router(me.router)

__all__ = ["router"]
