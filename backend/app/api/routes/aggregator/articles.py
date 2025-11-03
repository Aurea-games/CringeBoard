from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.routes.auth import dependencies as auth_dependencies

from . import dependencies as aggregator_dependencies
from . import schemas

router = APIRouter(prefix="/v1/articles", tags=["articles"])

CurrentUserEmail = Annotated[str, Depends(auth_dependencies.get_current_email)]


@router.get(
    "/{article_id}",
    response_model=schemas.Article,
)
def get_article(article_id: int) -> schemas.Article:
    return aggregator_dependencies.aggregator_service.get_article(article_id)


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
