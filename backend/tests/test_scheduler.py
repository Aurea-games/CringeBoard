"""Unit tests for scheduler module."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, call, patch

import pytest
from app.scheduler import build_scrapers, main


class MockSettings:
    """Mock settings for testing."""

    def __init__(
        self,
        rss_feeds: tuple[str, ...] = (),
        flipboard_magazines: tuple[str, ...] = (),
        flipboard_accounts: tuple[str, ...] = (),
        scheduler_interval: int = 1,
    ):
        self.rss_feeds = rss_feeds
        self.flipboard_magazines = flipboard_magazines
        self.flipboard_accounts = flipboard_accounts
        self.scheduler_interval = scheduler_interval
        self.project_name = "Test"
        self.aggregator_user_email = "test@test.com"
        self.aggregator_user_password = "password"


class TestBuildScrapers:
    """Test build_scrapers function."""

    def test_build_scrapers_empty_settings(self):
        settings = MockSettings()

        result = build_scrapers(settings)

        assert result == []

    def test_build_scrapers_with_rss_feed_single_part(self):
        settings = MockSettings(rss_feeds=("https://example.com/feed",))

        result = build_scrapers(settings)

        assert len(result) == 1
        assert result[0].newspaper_title == "https://example.com/feed"
        assert result[0]._feed_url == "https://example.com/feed"

    def test_build_scrapers_with_rss_feed_two_parts(self):
        settings = MockSettings(rss_feeds=("My Feed | https://example.com/feed",))

        result = build_scrapers(settings)

        assert len(result) == 1
        assert result[0].newspaper_title == "My Feed"
        assert result[0]._feed_url == "https://example.com/feed"
        assert result[0].newspaper_description is None

    def test_build_scrapers_with_rss_feed_three_parts(self):
        settings = MockSettings(rss_feeds=("My Feed | https://example.com/feed | A great feed",))

        result = build_scrapers(settings)

        assert len(result) == 1
        assert result[0].newspaper_title == "My Feed"
        assert result[0]._feed_url == "https://example.com/feed"
        assert result[0].newspaper_description == "A great feed"

    def test_build_scrapers_with_empty_rss_feed(self):
        settings = MockSettings(rss_feeds=("",))

        result = build_scrapers(settings)

        assert result == []

    def test_build_scrapers_with_multiple_rss_feeds(self):
        settings = MockSettings(
            rss_feeds=(
                "Feed 1 | https://feed1.com",
                "Feed 2 | https://feed2.com | Description 2",
            )
        )

        result = build_scrapers(settings)

        assert len(result) == 2

    def test_build_scrapers_with_flipboard_magazine(self):
        settings = MockSettings(flipboard_magazines=("tech/technology",))

        result = build_scrapers(settings)

        assert len(result) == 1
        # FlipboardMagazineScraper

    def test_build_scrapers_with_empty_flipboard_magazine(self):
        settings = MockSettings(flipboard_magazines=("",))

        result = build_scrapers(settings)

        assert result == []

    def test_build_scrapers_with_flipboard_account(self):
        settings = MockSettings(flipboard_accounts=("techcrunch",))

        result = build_scrapers(settings)

        assert len(result) == 1
        # FlipboardAccountScraper

    def test_build_scrapers_with_empty_flipboard_account(self):
        settings = MockSettings(flipboard_accounts=("",))

        result = build_scrapers(settings)

        assert result == []

    def test_build_scrapers_with_all_types(self):
        settings = MockSettings(
            rss_feeds=("RSS Feed | https://rss.com/feed",),
            flipboard_magazines=("tech/tech",),
            flipboard_accounts=("account1",),
        )

        result = build_scrapers(settings)

        assert len(result) == 3

    def test_build_scrapers_strips_whitespace(self):
        settings = MockSettings(rss_feeds=("  My Feed  |  https://example.com/feed  ",))

        result = build_scrapers(settings)

        assert len(result) == 1
        assert result[0].newspaper_title == "My Feed"
        assert result[0]._feed_url == "https://example.com/feed"


class TestMain:
    """Test main scheduler function."""

    def test_main_runs_aggregator(self):
        """Test that main runs the aggregator once and then we interrupt it."""
        mock_settings = MockSettings(scheduler_interval=0)
        mock_aggregator = MagicMock()
        mock_scrapers = []

        with (
            patch("app.scheduler.get_settings", return_value=mock_settings),
            patch("app.scheduler.build_scrapers", return_value=mock_scrapers),
            patch("app.scheduler.FeedAggregator", return_value=mock_aggregator) as mock_agg_class,
            patch("app.scheduler.AggregatorRepository"),
            patch("app.scheduler.AuthRepository"),
            patch("app.scheduler.PasswordHasher"),
            patch("app.scheduler.time.sleep", side_effect=KeyboardInterrupt),
            patch("builtins.print"),
        ):
            with pytest.raises(KeyboardInterrupt):
                main()

            # Verify aggregator.run was called
            mock_aggregator.run.assert_called_once()

    def test_main_handles_aggregation_exception(self):
        """Test that main catches exceptions from aggregator.run."""
        mock_settings = MockSettings(scheduler_interval=0)
        mock_aggregator = MagicMock()
        mock_aggregator.run.side_effect = [Exception("Test error"), KeyboardInterrupt]

        with (
            patch("app.scheduler.get_settings", return_value=mock_settings),
            patch("app.scheduler.build_scrapers", return_value=[]),
            patch("app.scheduler.FeedAggregator", return_value=mock_aggregator),
            patch("app.scheduler.AggregatorRepository"),
            patch("app.scheduler.AuthRepository"),
            patch("app.scheduler.PasswordHasher"),
            patch("app.scheduler.time.sleep", side_effect=[None, KeyboardInterrupt]),
            patch("builtins.print") as mock_print,
        ):
            with pytest.raises(KeyboardInterrupt):
                main()

            # Verify exception was caught and logged
            assert mock_aggregator.run.call_count >= 1

    def test_main_creates_aggregator_with_correct_args(self):
        """Test that main creates FeedAggregator with the correct arguments."""
        mock_settings = MockSettings(scheduler_interval=0)
        mock_scrapers = [MagicMock()]
        mock_repo = MagicMock()
        mock_auth_repo = MagicMock()
        mock_hasher = MagicMock()

        with (
            patch("app.scheduler.get_settings", return_value=mock_settings),
            patch("app.scheduler.build_scrapers", return_value=mock_scrapers),
            patch("app.scheduler.FeedAggregator") as mock_agg_class,
            patch("app.scheduler.AggregatorRepository", return_value=mock_repo),
            patch("app.scheduler.AuthRepository", return_value=mock_auth_repo),
            patch("app.scheduler.PasswordHasher", return_value=mock_hasher),
            patch("app.scheduler.time.sleep", side_effect=KeyboardInterrupt),
            patch("builtins.print"),
        ):
            with pytest.raises(KeyboardInterrupt):
                main()

            mock_agg_class.assert_called_once_with(
                a_repository=mock_repo,
                a_auth_repository=mock_auth_repo,
                a_password_hasher=mock_hasher,
                a_scrapers=mock_scrapers,
            )

    def test_main_uses_settings_interval(self):
        """Test that main uses the scheduler_interval from settings."""
        mock_settings = MockSettings(scheduler_interval=300)
        mock_aggregator = MagicMock()
        sleep_calls = []

        def track_sleep(seconds):
            sleep_calls.append(seconds)
            raise KeyboardInterrupt

        with (
            patch("app.scheduler.get_settings", return_value=mock_settings),
            patch("app.scheduler.build_scrapers", return_value=[]),
            patch("app.scheduler.FeedAggregator", return_value=mock_aggregator),
            patch("app.scheduler.AggregatorRepository"),
            patch("app.scheduler.AuthRepository"),
            patch("app.scheduler.PasswordHasher"),
            patch("app.scheduler.time.sleep", side_effect=track_sleep),
            patch("builtins.print"),
        ):
            with pytest.raises(KeyboardInterrupt):
                main()

            assert 300 in sleep_calls

    def test_main_prints_startup_message(self):
        """Test that main prints the startup message with interval."""
        mock_settings = MockSettings(scheduler_interval=60)
        mock_aggregator = MagicMock()

        printed_messages = []

        def capture_print(*args, **kwargs):
            printed_messages.append(" ".join(str(a) for a in args))

        with (
            patch("app.scheduler.get_settings", return_value=mock_settings),
            patch("app.scheduler.build_scrapers", return_value=[]),
            patch("app.scheduler.FeedAggregator", return_value=mock_aggregator),
            patch("app.scheduler.AggregatorRepository"),
            patch("app.scheduler.AuthRepository"),
            patch("app.scheduler.PasswordHasher"),
            patch("app.scheduler.time.sleep", side_effect=KeyboardInterrupt),
            patch("builtins.print", side_effect=capture_print),
        ):
            with pytest.raises(KeyboardInterrupt):
                main()

            # Check startup message was printed
            assert any("Scheduler started" in msg for msg in printed_messages)
            assert any("60" in msg for msg in printed_messages)

    def test_main_prints_running_message(self):
        """Test that main prints the running message each iteration."""
        mock_settings = MockSettings(scheduler_interval=0)
        mock_aggregator = MagicMock()

        printed_messages = []

        def capture_print(*args, **kwargs):
            printed_messages.append(" ".join(str(a) for a in args))

        with (
            patch("app.scheduler.get_settings", return_value=mock_settings),
            patch("app.scheduler.build_scrapers", return_value=[]),
            patch("app.scheduler.FeedAggregator", return_value=mock_aggregator),
            patch("app.scheduler.AggregatorRepository"),
            patch("app.scheduler.AuthRepository"),
            patch("app.scheduler.PasswordHasher"),
            patch("app.scheduler.time.sleep", side_effect=KeyboardInterrupt),
            patch("builtins.print", side_effect=capture_print),
        ):
            with pytest.raises(KeyboardInterrupt):
                main()

            # Check running message was printed
            assert any("running feed aggregation" in msg for msg in printed_messages)
