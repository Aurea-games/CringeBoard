from secrets import token_urlsafe
from typing import Callable, Optional

import bcrypt
from fastapi import HTTPException, status

from .repository import AuthRepository


class PasswordHasher:
    """Wrapper around bcrypt to hash and verify user passwords."""

    def hash(self, password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except (ValueError, TypeError):
            return False


class AuthService:
    """High-level authentication workflow built on top of repository and utilities."""

    _BLOCKED_SUFFIXES = ("@example.com",)

    def __init__(
        self,
        repository: AuthRepository,
        hasher: PasswordHasher,
        token_generator: Optional[Callable[[int], str]] = None,
    ) -> None:
        self._repository = repository
        self._hasher = hasher
        self._token_generator = token_generator or token_urlsafe

    def register_user(self, email: str, password: str) -> "TokenResponse":
        self._ensure_email_allowed(email)

        if self._repository.email_exists(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email is already registered.",
            )

        password_hash = self._hasher.hash(password)
        user_id = self._repository.create_user(email, password_hash)
        return self._issue_tokens(user_id)

    def authenticate(self, email: str, password: str) -> "TokenResponse":
        credentials = self._repository.get_user_credentials(email)

        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials.",
            )

        user_id, stored_hash = credentials

        if not self._hasher.verify(password, stored_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials.",
            )

        return self._issue_tokens(user_id)

    def remove_user(self, email: str) -> None:
        user_id = self._repository.get_user_id(email)
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        self._repository.delete_tokens_for_user(user_id)

        if not self._repository.delete_user(user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

    def _ensure_email_allowed(self, email: str) -> None:
        if email.endswith(self._BLOCKED_SUFFIXES):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration with example.com emails is not allowed.",
            )

    def _issue_tokens(self, user_id: int) -> "TokenResponse":
        access_token = self._token_generator(32)
        refresh_token = self._token_generator(48)
        self._repository.store_tokens(user_id, access_token, refresh_token)
        from .schemas import TokenResponse  # local import to avoid circular dependency

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )


__all__ = ["AuthService", "PasswordHasher"]
