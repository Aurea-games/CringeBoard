from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.security import HTTPAuthorizationCredentials

from app.api.routes.auth import dependencies as auth_dependencies

from . import dependencies as aggregator_dependencies
from . import schemas

router = APIRouter(prefix="/v1/sources", tags=["sources"])


def _get_optional_email(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(auth_dependencies.bearer_scheme),
    ],
) -> str | None:
    if credentials is None:
        return None
    token = credentials.credentials.strip()
    email = auth_dependencies.auth_repository.get_email_by_access_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
        )
    return email


CurrentUserEmail = Annotated[str, Depends(auth_dependencies.get_current_email)]
OptionalUserEmail = Annotated[str | None, Depends(_get_optional_email)]


@router.get("/", response_model=list[schemas.Source])
def list_sources(
    search: str | None = Query(default=None, alias="q"),
    status: str | None = Query(default=None),
    follower_email: OptionalUserEmail = None,
) -> list[schemas.Source]:
    return aggregator_dependencies.aggregator_service.list_sources(
        search=search,
        status=status,
        follower_email=follower_email,
    )


@router.post(
    "/",
    response_model=schemas.Source,
    status_code=status.HTTP_201_CREATED,
)
def create_source(
    payload: schemas.SourceCreate,
    current_email: CurrentUserEmail,
) -> schemas.Source:
    # current_email kept for parity with other endpoints (e.g., auditing later)
    return aggregator_dependencies.aggregator_service.create_source(payload)


@router.get(
    "/{source_id}",
    response_model=schemas.Source,
)
def get_source(
    source_id: int,
    follower_email: OptionalUserEmail = None,
) -> schemas.Source:
    return aggregator_dependencies.aggregator_service.get_source(source_id, follower_email)


@router.patch(
    "/{source_id}",
    response_model=schemas.Source,
)
def update_source(
    source_id: int,
    payload: schemas.SourceUpdate,
    current_email: CurrentUserEmail,
) -> schemas.Source:
    return aggregator_dependencies.aggregator_service.update_source(source_id, payload)


@router.post(
    "/{source_id}/follow",
    response_model=schemas.Source,
)
def follow_source(
    source_id: int,
    current_email: CurrentUserEmail,
) -> schemas.Source:
    return aggregator_dependencies.aggregator_service.follow_source(source_id, current_email)


@router.delete(
    "/{source_id}/follow",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unfollow_source(
    source_id: int,
    current_email: CurrentUserEmail,
) -> Response:
    aggregator_dependencies.aggregator_service.unfollow_source(source_id, current_email)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


__all__ = ["router"]
