"""Unit tests for auth dependencies."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from app.api.routes.auth.dependencies import get_bearer_scheme, get_current_email
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


class TestGetBearerScheme:
    """Test get_bearer_scheme function."""

    def test_get_bearer_scheme_returns_scheme(self):
        scheme = get_bearer_scheme()
        assert scheme is not None


class TestGetCurrentEmail:
    """Test get_current_email dependency."""

    def test_get_current_email_missing_credentials(self):
        with pytest.raises(HTTPException) as exc_info:
            get_current_email(None)

        assert exc_info.value.status_code == 401
        assert "Authorization header missing" in exc_info.value.detail

    def test_get_current_email_invalid_token(self):
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_token")

        with patch("app.api.routes.auth.dependencies.auth_repository") as mock_repo:
            mock_repo.get_email_by_access_token.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                get_current_email(credentials)

            assert exc_info.value.status_code == 401
            assert "Invalid or expired access token" in exc_info.value.detail

    def test_get_current_email_valid_token(self):
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token")

        with patch("app.api.routes.auth.dependencies.auth_repository") as mock_repo:
            mock_repo.get_email_by_access_token.return_value = "user@test.com"

            result = get_current_email(credentials)

            assert result == "user@test.com"

    def test_get_current_email_strips_token(self):
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="  token_with_spaces  ")

        with patch("app.api.routes.auth.dependencies.auth_repository") as mock_repo:
            mock_repo.get_email_by_access_token.return_value = "user@test.com"

            _ = get_current_email(credentials)

            mock_repo.get_email_by_access_token.assert_called_once_with("token_with_spaces")
