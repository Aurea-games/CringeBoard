from fastapi import APIRouter, status

from .dependencies import auth_service
from .schemas import RegisterRequest, TokenResponse

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=TokenResponse)
def register(payload: RegisterRequest) -> TokenResponse:
    return auth_service.register_user(payload.email, payload.password)


__all__ = ["router"]
