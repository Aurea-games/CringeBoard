"""Unit tests for auth profile routes."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def register_user(client: TestClient, email: str = "user@valid.com", password: str = "password123") -> dict:
    """Helper to register a user."""
    response = client.post(
        "/v1/auth/register",
        json={"email": email, "password": password, "confirm_password": password},
    )
    assert response.status_code == 201, f"Registration failed: {response.json()}"
    return response.json()


def auth_headers(tokens: dict) -> dict:
    """Helper to create auth headers."""
    return {"Authorization": f"Bearer {tokens['access_token']}"}


class TestProfileEndpoint:
    """Test /users/me endpoint."""

    def test_get_current_user(self, auth_test_client: TestClient):
        tokens = register_user(auth_test_client, "profileuser@valid.com")

        response = auth_test_client.get("/v1/auth/users/me", headers=auth_headers(tokens))

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "profileuser@valid.com"
        assert "id" in data

    def test_get_current_user_unauthorized(self, auth_test_client: TestClient):
        response = auth_test_client.get("/v1/auth/users/me")

        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, auth_test_client: TestClient):
        response = auth_test_client.get("/v1/auth/users/me", headers={"Authorization": "Bearer invalid_token"})

        assert response.status_code == 401
