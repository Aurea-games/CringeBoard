"""Unit tests for auth preferences routes."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

REGISTER_URL = "/v1/auth/register"
PREFERENCES_URL = "/v1/auth/users/me/preferences"
PREFERENCES_HIDE_URL = "/v1/auth/users/me/preferences/hide-source"


def register_user(client: TestClient, email: str = "user@valid.com", password: str = "password123") -> dict:
    """Helper to register a user."""
    response = client.post(
        REGISTER_URL,
        json={"email": email, "password": password, "confirm_password": password},
    )
    assert response.status_code == 201, f"Registration failed: {response.json()}"
    return response.json()


def auth_headers(tokens: dict) -> dict:
    """Helper to create auth headers."""
    return {"Authorization": f"Bearer {tokens['access_token']}"}


class TestPreferencesEndpoint:
    """Test preferences endpoints."""

    def test_get_preferences(self, auth_test_client: TestClient):
        tokens = register_user(auth_test_client, "prefuser@valid.com")

        response = auth_test_client.get(PREFERENCES_URL, headers=auth_headers(tokens))

        assert response.status_code == 200
        data = response.json()
        assert "theme" in data
        assert "hidden_source_ids" in data

    def test_get_preferences_unauthorized(self, auth_test_client: TestClient):
        response = auth_test_client.get(PREFERENCES_URL)
        assert response.status_code == 401

    def test_update_preferences_theme(self, auth_test_client: TestClient):
        tokens = register_user(auth_test_client, "prefuser2@valid.com")

        response = auth_test_client.put(
            PREFERENCES_URL,
            json={"theme": "dark"},
            headers=auth_headers(tokens),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["theme"] == "dark"

    def test_update_preferences_hidden_sources(self, auth_test_client: TestClient):
        tokens = register_user(auth_test_client, "prefuser3@valid.com")

        response = auth_test_client.put(
            PREFERENCES_URL,
            json={"hidden_source_ids": [1, 2, 3]},
            headers=auth_headers(tokens),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["hidden_source_ids"] == [1, 2, 3]

    def test_add_hidden_source(self, auth_test_client: TestClient):
        tokens = register_user(auth_test_client, "prefuser4@valid.com")

        response = auth_test_client.post(
            PREFERENCES_HIDE_URL,
            json={"source_id": 5},
            headers=auth_headers(tokens),
        )

        assert response.status_code == 200
        data = response.json()
        assert 5 in data["hidden_source_ids"]

    def test_remove_hidden_source(self, auth_test_client: TestClient):
        tokens = register_user(auth_test_client, "prefuser5@valid.com")

        # First add a hidden source
        auth_test_client.post(
            PREFERENCES_HIDE_URL,
            json={"source_id": 10},
            headers=auth_headers(tokens),
        )

        # Then remove it
        response = auth_test_client.delete(
            f"{PREFERENCES_HIDE_URL}/10",
            headers=auth_headers(tokens),
        )

        assert response.status_code == 200
        data = response.json()
        assert 10 not in data["hidden_source_ids"]
