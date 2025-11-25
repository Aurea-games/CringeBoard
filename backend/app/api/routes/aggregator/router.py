from fastapi import APIRouter

from . import articles, newspapers

router = APIRouter()
router.include_router(newspapers.router)
router.include_router(articles.router)

__all__ = ["router"]
