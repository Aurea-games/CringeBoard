from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.routes.auth import dependencies as auth_dependencies

from . import dependencies as aggregator_dependencies
from . import schemas

router = APIRouter(prefix="/v1/newspapers", tags=["newspapers"])


CurrentUserEmail = Annotated[str, Depends(auth_dependencies.get_current_email)]


@router.get("/", response_model=list[schemas.Newspaper])
def list_newspapers(
    search: str | None = Query(default=None, alias="q"),
    owner_email: str | None = Query(default=None),
) -> list[schemas.Newspaper]:
    return aggregator_dependencies.aggregator_service.list_newspapers(search, owner_email)


@router.post(
    "/",
    response_model=schemas.Newspaper,
    status_code=status.HTTP_201_CREATED,
)
def create_newspaper(
    payload: schemas.NewspaperCreate,
    current_email: CurrentUserEmail,
) -> schemas.Newspaper:
    return aggregator_dependencies.aggregator_service.create_newspaper(current_email, payload)


@router.get(
    "/{newspaper_id}",
    response_model=schemas.NewspaperDetail,
)
def get_newspaper(newspaper_id: int) -> schemas.NewspaperDetail:
    return aggregator_dependencies.aggregator_service.get_newspaper(newspaper_id)


@router.patch(
    "/{newspaper_id}",
    response_model=schemas.Newspaper,
)
def update_newspaper(
    newspaper_id: int,
    payload: schemas.NewspaperUpdate,
    current_email: CurrentUserEmail,
) -> schemas.Newspaper:
    return aggregator_dependencies.aggregator_service.update_newspaper(newspaper_id, current_email, payload)


@router.delete(
    "/{newspaper_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_newspaper(
    newspaper_id: int,
    current_email: CurrentUserEmail,
) -> Response:
    aggregator_dependencies.aggregator_service.delete_newspaper(newspaper_id, current_email)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{newspaper_id}/articles",
    response_model=list[schemas.Article],
)
def list_articles(
    newspaper_id: int,
    search: str | None = Query(default=None, alias="q"),
) -> list[schemas.Article]:
    return aggregator_dependencies.aggregator_service.list_articles_for_newspaper(newspaper_id, search)


@router.post(
    "/{newspaper_id}/articles",
    response_model=schemas.Article,
    status_code=status.HTTP_201_CREATED,
)
def create_article(
    newspaper_id: int,
    payload: schemas.ArticleCreate,
    current_email: CurrentUserEmail,
) -> schemas.Article:
    return aggregator_dependencies.aggregator_service.create_article(newspaper_id, current_email, payload)


@router.post(
    "/{newspaper_id}/articles/{article_id}",
    response_model=schemas.Article,
)
def attach_existing_article(
    newspaper_id: int,
    article_id: int,
    current_email: CurrentUserEmail,
) -> schemas.Article:
    return aggregator_dependencies.aggregator_service.attach_article_to_newspaper(
        newspaper_id,
        article_id,
        current_email,
    )


@router.delete(
    "/{newspaper_id}/articles/{article_id}",
    response_model=schemas.Article,
)
def detach_existing_article(
    newspaper_id: int,
    article_id: int,
    current_email: CurrentUserEmail,
) -> schemas.Article:
    return aggregator_dependencies.aggregator_service.detach_article_from_newspaper(
        newspaper_id,
        article_id,
        current_email,
    )
