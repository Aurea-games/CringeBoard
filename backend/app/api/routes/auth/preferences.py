from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from . import dependencies, schemas

router = APIRouter()

CurrentEmail = Annotated[str, Depends(dependencies.get_current_email)]


def _get_user_id(email: str) -> int:
    user_id = dependencies.auth_repository.get_user_id(email)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return user_id


@router.get(
    "/users/me/preferences",
    response_model=schemas.Preferences,
)
def get_preferences(current_email: CurrentEmail) -> schemas.Preferences:
    user_id = _get_user_id(current_email)
    prefs = dependencies.auth_repository.get_preferences(user_id)
    return schemas.Preferences.model_validate(prefs)


@router.put(
    "/users/me/preferences",
    response_model=schemas.Preferences,
)
def update_preferences(
    payload: schemas.PreferencesUpdate,
    current_email: CurrentEmail,
) -> schemas.Preferences:
    user_id = _get_user_id(current_email)
    prefs = dependencies.auth_repository.update_preferences(
        user_id=user_id,
        theme=payload.theme,
        hidden_source_ids=payload.hidden_source_ids,
    )
    return schemas.Preferences.model_validate(prefs)


@router.post(
    "/users/me/preferences/hide-source",
    response_model=schemas.Preferences,
    status_code=status.HTTP_200_OK,
)
def hide_source(
    payload: schemas.SourceToggleRequest,
    current_email: CurrentEmail,
) -> schemas.Preferences:
    user_id = _get_user_id(current_email)
    prefs = dependencies.auth_repository.add_hidden_source(user_id, payload.source_id)
    return schemas.Preferences.model_validate(prefs)


@router.delete(
    "/users/me/preferences/hide-source/{source_id}",
    response_model=schemas.Preferences,
)
def unhide_source(
    source_id: int,
    current_email: CurrentEmail,
) -> schemas.Preferences:
    if source_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="source_id must be greater than zero.",
        )
    user_id = _get_user_id(current_email)
    prefs = dependencies.auth_repository.remove_hidden_source(user_id, source_id)
    return schemas.Preferences.model_validate(prefs)


__all__ = ["router"]
