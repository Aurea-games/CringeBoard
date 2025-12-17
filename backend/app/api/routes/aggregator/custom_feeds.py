from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.routes.auth import dependencies as auth_dependencies

from . import dependencies as aggregator_dependencies
from . import schemas

router = APIRouter(prefix="/v1/custom-feeds", tags=["custom-feeds"])


CurrentUserEmail = Annotated[str, Depends(auth_dependencies.get_current_email)]


@router.get("/", response_model=list[schemas.CustomFeed])
def list_custom_feeds(
    current_email: CurrentUserEmail,
) -> list[schemas.CustomFeed]:
    """List all custom feeds for the current user."""
    return aggregator_dependencies.aggregator_service.list_custom_feeds(current_email)


@router.post(
    "/",
    response_model=schemas.CustomFeed,
    status_code=status.HTTP_201_CREATED,
)
def create_custom_feed(
    payload: schemas.CustomFeedCreate,
    current_email: CurrentUserEmail,
) -> schemas.CustomFeed:
    """Create a new custom feed with filter rules."""
    return aggregator_dependencies.aggregator_service.create_custom_feed(current_email, payload)


@router.post(
    "/preview",
    response_model=list[schemas.Article],
)
def preview_custom_feed(
    payload: schemas.CustomFeedFilterRules,
    current_email: CurrentUserEmail,
    limit: int = Query(default=20, ge=1, le=100),
) -> list[schemas.Article]:
    """Preview articles that would match the given filter rules without saving."""
    return aggregator_dependencies.aggregator_service.preview_custom_feed(
        owner_email=current_email,
        filter_rules=payload,
        limit=limit,
    )


@router.get(
    "/{custom_feed_id}",
    response_model=schemas.CustomFeed,
)
def get_custom_feed(
    custom_feed_id: int,
    current_email: CurrentUserEmail,
) -> schemas.CustomFeed:
    """Get a custom feed by ID."""
    return aggregator_dependencies.aggregator_service.get_custom_feed(custom_feed_id, current_email)


@router.get(
    "/{custom_feed_id}/articles",
    response_model=schemas.CustomFeedWithArticles,
)
def get_custom_feed_articles(
    custom_feed_id: int,
    current_email: CurrentUserEmail,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> schemas.CustomFeedWithArticles:
    """Get a custom feed with its matching articles."""
    return aggregator_dependencies.aggregator_service.get_custom_feed_articles(
        custom_feed_id=custom_feed_id,
        owner_email=current_email,
        limit=limit,
        offset=offset,
    )


@router.patch(
    "/{custom_feed_id}",
    response_model=schemas.CustomFeed,
)
def update_custom_feed(
    custom_feed_id: int,
    payload: schemas.CustomFeedUpdate,
    current_email: CurrentUserEmail,
) -> schemas.CustomFeed:
    """Update a custom feed's name, description, or filter rules."""
    return aggregator_dependencies.aggregator_service.update_custom_feed(
        custom_feed_id=custom_feed_id,
        owner_email=current_email,
        payload=payload,
    )


@router.delete(
    "/{custom_feed_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_custom_feed(
    custom_feed_id: int,
    current_email: CurrentUserEmail,
) -> Response:
    """Delete a custom feed."""
    aggregator_dependencies.aggregator_service.delete_custom_feed(custom_feed_id, current_email)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
