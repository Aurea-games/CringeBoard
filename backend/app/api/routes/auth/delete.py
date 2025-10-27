from fastapi import APIRouter, Depends, status

from .dependencies import auth_service, get_current_email

router = APIRouter()


@router.delete("/users/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(current_email: str = Depends(get_current_email)) -> None:
    auth_service.remove_user(current_email)


__all__ = ["router"]
