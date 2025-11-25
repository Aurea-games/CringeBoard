from fastapi import APIRouter, Depends

from .dependencies import get_current_email, auth_repository

router = APIRouter()


@router.get("/users/me")
def get_current_user(current_email: str = Depends(get_current_email)) -> dict:
    # Return basic info about the authenticated user
    user_id = auth_repository.get_user_id(current_email)
    return {"email": current_email, "id": user_id}


__all__ = ["router"]
