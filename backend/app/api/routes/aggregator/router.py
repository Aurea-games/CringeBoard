from fastapi import APIRouter

from . import articles, custom_feeds, me, newspapers, public, sources

router = APIRouter()
router.include_router(newspapers.router)
router.include_router(articles.router)
router.include_router(sources.router)
router.include_router(custom_feeds.router)
router.include_router(me.router)
router.include_router(public.router)

__all__ = ["router"]
