"""Unit tests for system routes."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


class MockSettings:
    """Mock settings for testing."""

    def __init__(self, project_name: str = "Test Project"):
        self.project_name = project_name


def test_read_root(auth_test_client: TestClient):
    """Test the root endpoint returns project name and status."""
    response = auth_test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["status"] == "ok"


def test_healthz(auth_test_client: TestClient):
    """Test the health check endpoint."""
    response = auth_test_client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthyyyy"


def test_read_root_returns_project_name():
    """Test root endpoint with mocked settings."""
    from app.api.routes.system import read_root

    with patch("app.api.routes.system.get_settings", return_value=MockSettings("My Custom Project")):
        result = read_root()
        assert result["name"] == "My Custom Project"
        assert result["status"] == "ok"


def test_healthz_returns_healthy():
    """Test healthz endpoint directly."""
    from app.api.routes.system import healthz

    result = healthz()
    assert result["status"] == "healthyyyy"
