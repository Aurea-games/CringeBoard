"""Unit tests for auth validators."""

from __future__ import annotations

import pytest
from app.api.routes.auth.validators import normalize_email


class TestNormalizeEmail:
    """Test normalize_email function."""

    def test_normalize_email_valid(self):
        result = normalize_email("User@Example.COM")
        assert result == "user@example.com"

    def test_normalize_email_strips_whitespace(self):
        result = normalize_email("  user@example.com  ")
        assert result == "user@example.com"

    def test_normalize_email_none_raises(self):
        with pytest.raises(ValueError) as exc_info:
            normalize_email(None)
        assert "Email is required" in str(exc_info.value)

    def test_normalize_email_empty_raises(self):
        with pytest.raises(ValueError) as exc_info:
            normalize_email("")
        assert "Invalid email format" in str(exc_info.value)

    def test_normalize_email_whitespace_only_raises(self):
        with pytest.raises(ValueError) as exc_info:
            normalize_email("   ")
        assert "Invalid email format" in str(exc_info.value)

    def test_normalize_email_invalid_format_raises(self):
        with pytest.raises(ValueError) as exc_info:
            normalize_email("not-an-email")
        assert "Invalid email format" in str(exc_info.value)

    def test_normalize_email_missing_domain_raises(self):
        with pytest.raises(ValueError) as exc_info:
            normalize_email("user@")
        assert "Invalid email format" in str(exc_info.value)

    def test_normalize_email_missing_tld_raises(self):
        with pytest.raises(ValueError) as exc_info:
            normalize_email("user@domain")
        assert "Invalid email format" in str(exc_info.value)

    def test_normalize_email_with_plus(self):
        result = normalize_email("user+tag@example.com")
        assert result == "user+tag@example.com"

    def test_normalize_email_with_dots(self):
        result = normalize_email("user.name@example.com")
        assert result == "user.name@example.com"

    def test_normalize_email_with_numbers(self):
        result = normalize_email("user123@example123.com")
        assert result == "user123@example123.com"

    def test_normalize_email_subdomain(self):
        result = normalize_email("user@mail.example.com")
        assert result == "user@mail.example.com"
