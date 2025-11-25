from fastapi import APIRouter, HTTPException, status

from .dependencies import auth_service
from .schemas import LoginRequest, TokenResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    if not payload.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must not be empty.",
        )

    return auth_service.authenticate(payload.email, payload.password)


__all__ = ["router"]
