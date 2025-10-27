from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .repository import AuthRepository
from .services import AuthService, PasswordHasher
from .validators import normalize_email

password_hasher = PasswordHasher()
auth_repository = AuthRepository()
auth_service = AuthService(auth_repository, password_hasher)
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_email(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing.",
        )

    normalized_token = credentials.credentials.strip()
    email = auth_repository.get_email_by_access_token(normalized_token)

    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
        )

    return normalize_email(email)


__all__ = ["auth_service", "bearer_scheme", "get_current_email"]
