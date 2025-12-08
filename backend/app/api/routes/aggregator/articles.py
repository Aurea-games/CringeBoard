from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.routes.auth import dependencies as auth_dependencies

from . import dependencies as aggregator_dependencies
from . import schemas

router = APIRouter(prefix="/v1/articles", tags=["articles"])

CurrentUserEmail = Annotated[str, Depends(auth_dependencies.get_current_email)]


@router.get(
    "/",
    response_model=list[schemas.Article],
)
def search_articles(
    search: str | None = Query(default=None, alias="q"),
    owner_email: str | None = Query(default=None),
    newspaper_id: int | None = Query(default=None),
) -> list[schemas.Article]:
    return aggregator_dependencies.aggregator_service.search_articles(
        search=search,
        owner_email=owner_email,
        newspaper_id=newspaper_id,
    )


@router.get(
    "/popular",
    response_model=list[schemas.Article],
)
def list_popular_articles(
    search: str | None = Query(default=None, alias="q"),
    owner_email: str | None = Query(default=None),
    newspaper_id: int | None = Query(default=None),
) -> list[schemas.Article]:
    return aggregator_dependencies.aggregator_service.search_articles(
        search=search,
        owner_email=owner_email,
        newspaper_id=newspaper_id,
        order_by_popularity=True,
    )


@router.get(
    "/{article_id}",
    response_model=schemas.Article,
)
def get_article(article_id: int) -> schemas.Article:
    return aggregator_dependencies.aggregator_service.get_article(article_id)


@router.get(
    "/{article_id}/related",
    response_model=list[schemas.Article],
)
def list_related_articles(
    article_id: int,
    limit: int = Query(default=10, ge=1, le=50),
) -> list[schemas.Article]:
    return aggregator_dependencies.aggregator_service.list_related_articles(article_id, limit=limit)


@router.post(
    "/{article_id}/favorite",
    response_model=schemas.Article,
)
def favorite_article(
    article_id: int,
    current_email: CurrentUserEmail,
) -> schemas.Article:
    return aggregator_dependencies.aggregator_service.favorite_article(article_id, current_email)


@router.delete(
    "/{article_id}/favorite",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unfavorite_article(
    article_id: int,
    current_email: CurrentUserEmail,
) -> Response:
    aggregator_dependencies.aggregator_service.unfavorite_article(article_id, current_email)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{article_id}/read-later",
    response_model=schemas.Article,
)
def mark_article_for_later(
    article_id: int,
    current_email: CurrentUserEmail,
) -> schemas.Article:
    return aggregator_dependencies.aggregator_service.save_article_for_later(article_id, current_email)


@router.delete(
    "/{article_id}/read-later",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unmark_article_for_later(
    article_id: int,
    current_email: CurrentUserEmail,
) -> Response:
    aggregator_dependencies.aggregator_service.remove_article_from_read_later(article_id, current_email)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{article_id}",
    response_model=schemas.Article,
)
def update_article(
    article_id: int,
    payload: schemas.ArticleUpdate,
    current_email: CurrentUserEmail,
) -> schemas.Article:
    return aggregator_dependencies.aggregator_service.update_article(article_id, current_email, payload)


@router.delete(
    "/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_article(
    article_id: int,
    current_email: CurrentUserEmail,
) -> Response:
    aggregator_dependencies.aggregator_service.delete_article(article_id, current_email)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
