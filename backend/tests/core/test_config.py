"""Unit tests for core config module."""

from __future__ import annotations

import os
from unittest.mock import patch

from app.core.config import Settings, _parse_origins, get_settings


class TestParseOrigins:
    """Test _parse_origins function."""

    def test_parse_origins_single(self):
        result = _parse_origins("http://localhost:3000")
        assert result == ["http://localhost:3000"]

    def test_parse_origins_multiple(self):
        result = _parse_origins("http://localhost:3000,http://localhost:8080")
        assert result == ["http://localhost:3000", "http://localhost:8080"]

    def test_parse_origins_strips_whitespace(self):
        result = _parse_origins("  http://localhost:3000  ,  http://localhost:8080  ")
        assert result == ["http://localhost:3000", "http://localhost:8080"]

    def test_parse_origins_empty_string(self):
        result = _parse_origins("")
        assert result == []

    def test_parse_origins_filters_empty(self):
        result = _parse_origins("http://localhost:3000,,http://localhost:8080")
        assert result == ["http://localhost:3000", "http://localhost:8080"]


class TestSettings:
    """Test Settings dataclass."""

    def test_settings_defaults(self):
        settings = Settings()
        assert settings.project_name == "CringeBoard API"
        assert settings.cors_origins == ()
        assert settings.scheduler_interval == 60

    def test_settings_custom_values(self):
        settings = Settings(
            project_name="Custom Project",
            cors_origins=["http://localhost:3000"],
            scheduler_interval=120,
        )
        assert settings.project_name == "Custom Project"
        assert settings.cors_origins == ("http://localhost:3000",)
        assert settings.scheduler_interval == 120

    def test_settings_converts_cors_origins_to_tuple(self):
        settings = Settings(cors_origins=["http://localhost"])
        assert isinstance(settings.cors_origins, tuple)

    def test_settings_converts_flipboard_magazines_to_tuple(self):
        settings = Settings(flipboard_magazines=["tech/tech"])
        assert isinstance(settings.flipboard_magazines, tuple)

    def test_settings_converts_flipboard_accounts_to_tuple(self):
        settings = Settings(flipboard_accounts=["account1"])
        assert isinstance(settings.flipboard_accounts, tuple)

    def test_settings_converts_rss_feeds_to_tuple(self):
        settings = Settings(rss_feeds=["http://feed.url"])
        assert isinstance(settings.rss_feeds, tuple)

    def test_settings_handles_none_values(self):
        settings = Settings(
            cors_origins=None,
            flipboard_magazines=None,
            flipboard_accounts=None,
            rss_feeds=None,
        )
        assert settings.cors_origins == ()
        assert settings.flipboard_magazines == ()
        assert settings.flipboard_accounts == ()
        assert settings.rss_feeds == ()


class TestGetSettings:
    """Test get_settings function."""

    def test_get_settings_returns_settings(self):
        # Clear cache to test fresh settings
        get_settings.cache_clear()

        with patch.dict(os.environ, {}, clear=False):
            settings = get_settings()
            assert isinstance(settings, Settings)

    def test_get_settings_uses_env_vars(self):
        get_settings.cache_clear()

        with patch.dict(
            os.environ,
            {
                "PROJECT_NAME": "Test Project",
                "CORS_ORIGINS": "http://test.com",
                "SCHEDULER_INTERVAL": "300",
                "AGGREGATOR_USER_EMAIL": "test@test.com",
                "AGGREGATOR_USER_PASSWORD": "testpass",
            },
            clear=False,
        ):
            settings = get_settings()
            assert settings.project_name == "Test Project"
            assert "http://test.com" in settings.cors_origins
            assert settings.scheduler_interval == 300
            assert settings.aggregator_user_email == "test@test.com"
            assert settings.aggregator_user_password == "testpass"

    def test_get_settings_parses_flipboard_magazines(self):
        get_settings.cache_clear()

        with patch.dict(os.environ, {"FLIPBOARD_MAGAZINES": "tech/tech,news/news"}, clear=False):
            settings = get_settings()
            assert "tech/tech" in settings.flipboard_magazines
            assert "news/news" in settings.flipboard_magazines

    def test_get_settings_parses_rss_feeds(self):
        get_settings.cache_clear()

        with patch.dict(os.environ, {"RSS_FEEDS": "http://feed1.com,http://feed2.com"}, clear=False):
            settings = get_settings()
            assert "http://feed1.com" in settings.rss_feeds
            assert "http://feed2.com" in settings.rss_feeds

    def test_get_settings_is_cached(self):
        get_settings.cache_clear()

        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
