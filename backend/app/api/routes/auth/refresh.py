from fastapi import APIRouter, status

from .dependencies import auth_service
from .schemas import RefreshRequest, TokenResponse

router = APIRouter()


@router.post("/refresh", status_code=status.HTTP_200_OK, response_model=TokenResponse)
def refresh(payload: RefreshRequest) -> TokenResponse:
    return auth_service.refresh_tokens(payload.refresh_token)


__all__ = ["router"]
