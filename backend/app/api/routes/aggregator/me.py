from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.api.routes.auth import dependencies as auth_dependencies

from . import dependencies as aggregator_dependencies
from . import schemas

router = APIRouter(prefix="/v1/me", tags=["me"])

CurrentUserEmail = Annotated[str, Depends(auth_dependencies.get_current_email)]


class ArticleAction(BaseModel):
    """Request payload to target an article by id."""

    model_config = ConfigDict(populate_by_name=True)

    article_id: int = Field(
        ...,
        ge=1,
        validation_alias=AliasChoices("articleId", "article_id"),
        serialization_alias="articleId",
    )


@router.get(
    "/favorites",
    response_model=list[schemas.Article],
)
def list_favorites(current_email: CurrentUserEmail) -> list[schemas.Article]:
    return aggregator_dependencies.aggregator_service.list_favorite_articles(current_email)


@router.post(
    "/favorites",
    response_model=schemas.Article,
    status_code=status.HTTP_201_CREATED,
)
def add_favorite(
    payload: ArticleAction,
    current_email: CurrentUserEmail,
) -> schemas.Article:
    return aggregator_dependencies.aggregator_service.favorite_article(payload.article_id, current_email)


@router.delete(
    "/favorites/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_favorite(
    article_id: int,
    current_email: CurrentUserEmail,
) -> Response:
    aggregator_dependencies.aggregator_service.unfavorite_article(article_id, current_email)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/read-later",
    response_model=list[schemas.Article],
)
def list_read_later(current_email: CurrentUserEmail) -> list[schemas.Article]:
    return aggregator_dependencies.aggregator_service.list_read_later_articles(current_email)


@router.post(
    "/read-later",
    response_model=schemas.Article,
    status_code=status.HTTP_201_CREATED,
)
def add_read_later(
    payload: ArticleAction,
    current_email: CurrentUserEmail,
) -> schemas.Article:
    return aggregator_dependencies.aggregator_service.save_article_for_later(payload.article_id, current_email)


@router.delete(
    "/read-later/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_read_later(
    article_id: int,
    current_email: CurrentUserEmail,
) -> Response:
    aggregator_dependencies.aggregator_service.remove_article_from_read_later(article_id, current_email)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


__all__ = ["router"]
