"""Unit tests for FeedAggregator."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest
from app.aggregator.feed import FeedAggregator, ScrapedArticle


@dataclass(frozen=True)
class MockScrapedArticle:
    title: str
    url: str
    summary: str | None = None


class MockScraper:
    """Mock scraper for testing."""

    def __init__(self, title: str, description: str | None = None, articles: list | None = None):
        self._title = title
        self._description = description
        self._articles = articles or []

    @property
    def newspaper_title(self) -> str:
        return self._title

    @property
    def newspaper_description(self) -> str | None:
        return self._description

    def scrape(self):
        return self._articles


class MockSettings:
    """Mock settings for testing."""

    def __init__(self):
        self.aggregator_user_email = "aggregator@test.com"
        self.aggregator_user_password = "testpassword"


class TestScrapedArticle:
    """Test ScrapedArticle dataclass."""

    def test_scraped_article_creation(self):
        article = ScrapedArticle(title="Test", url="http://test.com", summary="Summary")
        assert article.title == "Test"
        assert article.url == "http://test.com"
        assert article.summary == "Summary"

    def test_scraped_article_default_summary(self):
        article = ScrapedArticle(title="Test", url="http://test.com")
        assert article.summary is None

    def test_scraped_article_is_frozen(self):
        article = ScrapedArticle(title="Test", url="http://test.com")
        with pytest.raises(AttributeError):
            article.title = "New Title"


class TestFeedAggregator:
    """Test FeedAggregator class."""

    def test_init(self):
        mock_repo = MagicMock()
        mock_auth_repo = MagicMock()
        mock_hasher = MagicMock()
        scrapers = [MockScraper("Test")]

        with patch("app.aggregator.feed.get_settings", return_value=MockSettings()):
            aggregator = FeedAggregator(mock_repo, mock_auth_repo, mock_hasher, scrapers)

            assert aggregator._repository is mock_repo
            assert aggregator._auth_repository is mock_auth_repo
            assert aggregator._password_hasher is mock_hasher
            assert len(aggregator._scrapers) == 1

    def test_ensure_system_user_existing(self):
        mock_repo = MagicMock()
        mock_auth_repo = MagicMock()
        mock_auth_repo.get_user_id.return_value = 42
        mock_hasher = MagicMock()

        with patch("app.aggregator.feed.get_settings", return_value=MockSettings()):
            aggregator = FeedAggregator(mock_repo, mock_auth_repo, mock_hasher, [])

            user_id = aggregator.ensure_system_user()

            assert user_id == 42
            mock_auth_repo.get_user_id.assert_called_once_with("aggregator@test.com")
            mock_auth_repo.create_user.assert_not_called()

    def test_ensure_system_user_creates_new(self):
        mock_repo = MagicMock()
        mock_auth_repo = MagicMock()
        mock_auth_repo.get_user_id.return_value = None
        mock_auth_repo.create_user.return_value = 99
        mock_hasher = MagicMock()
        mock_hasher.hash.return_value = "hashed_password"

        with patch("app.aggregator.feed.get_settings", return_value=MockSettings()):
            aggregator = FeedAggregator(mock_repo, mock_auth_repo, mock_hasher, [])

            user_id = aggregator.ensure_system_user()

            assert user_id == 99
            mock_hasher.hash.assert_called_once_with("testpassword")
            mock_auth_repo.create_user.assert_called_once_with("aggregator@test.com", "hashed_password")

    def test_ensure_newspaper_existing(self):
        mock_repo = MagicMock()
        mock_repo.find_newspaper_by_title.return_value = {"id": 1, "title": "Test"}
        mock_auth_repo = MagicMock()
        mock_hasher = MagicMock()
        scraper = MockScraper("Test Newspaper", "Description")

        with patch("app.aggregator.feed.get_settings", return_value=MockSettings()):
            aggregator = FeedAggregator(mock_repo, mock_auth_repo, mock_hasher, [])

            result = aggregator.ensure_newspaper(1, scraper)

            assert result["id"] == 1
            mock_repo.find_newspaper_by_title.assert_called_once_with(1, "Test Newspaper")
            mock_repo.create_newspaper.assert_not_called()

    def test_ensure_newspaper_creates_new(self):
        mock_repo = MagicMock()
        mock_repo.find_newspaper_by_title.return_value = None
        mock_repo.create_newspaper.return_value = {"id": 5, "title": "New Newspaper"}
        mock_auth_repo = MagicMock()
        mock_hasher = MagicMock()
        scraper = MockScraper("New Newspaper", "Description")

        with patch("app.aggregator.feed.get_settings", return_value=MockSettings()):
            aggregator = FeedAggregator(mock_repo, mock_auth_repo, mock_hasher, [])

            result = aggregator.ensure_newspaper(1, scraper)

            assert result["id"] == 5
            mock_repo.create_newspaper.assert_called_once_with(
                owner_id=1,
                title="New Newspaper",
                description="Description",
            )

    def test_run_creates_new_articles(self):
        mock_repo = MagicMock()
        mock_repo.find_newspaper_by_title.return_value = {"id": 1, "title": "Test"}
        mock_repo.find_article_by_url.return_value = None
        mock_auth_repo = MagicMock()
        mock_auth_repo.get_user_id.return_value = 1
        mock_hasher = MagicMock()

        articles = [
            ScrapedArticle(title="Article 1", url="http://example.com/1", summary="Summary 1"),
            ScrapedArticle(title="Article 2", url="http://example.com/2", summary="Summary 2"),
        ]
        scraper = MockScraper("Test", articles=articles)

        with patch("app.aggregator.feed.get_settings", return_value=MockSettings()):
            aggregator = FeedAggregator(mock_repo, mock_auth_repo, mock_hasher, [scraper])

            aggregator.run()

            assert mock_repo.create_article.call_count == 2

    def test_run_assigns_existing_articles(self):
        mock_repo = MagicMock()
        mock_repo.find_newspaper_by_title.return_value = {"id": 1, "title": "Test"}
        mock_repo.find_article_by_url.return_value = {"id": 100, "title": "Existing"}
        mock_auth_repo = MagicMock()
        mock_auth_repo.get_user_id.return_value = 1
        mock_hasher = MagicMock()

        articles = [
            ScrapedArticle(title="Existing Article", url="http://example.com/existing"),
        ]
        scraper = MockScraper("Test", articles=articles)

        with patch("app.aggregator.feed.get_settings", return_value=MockSettings()):
            aggregator = FeedAggregator(mock_repo, mock_auth_repo, mock_hasher, [scraper])

            aggregator.run()

            mock_repo.create_article.assert_not_called()
            mock_repo.assign_article_to_newspaper.assert_called_once_with(100, 1)

    def test_run_with_multiple_scrapers(self):
        mock_repo = MagicMock()
        mock_repo.find_newspaper_by_title.side_effect = [
            {"id": 1, "title": "Paper 1"},
            {"id": 2, "title": "Paper 2"},
        ]
        mock_repo.find_article_by_url.return_value = None
        mock_auth_repo = MagicMock()
        mock_auth_repo.get_user_id.return_value = 1
        mock_hasher = MagicMock()

        scraper1 = MockScraper("Paper 1", articles=[ScrapedArticle("Art 1", "http://1.com")])
        scraper2 = MockScraper("Paper 2", articles=[ScrapedArticle("Art 2", "http://2.com")])

        with patch("app.aggregator.feed.get_settings", return_value=MockSettings()):
            aggregator = FeedAggregator(mock_repo, mock_auth_repo, mock_hasher, [scraper1, scraper2])

            aggregator.run()

            assert mock_repo.create_article.call_count == 2

    def test_run_with_no_scrapers(self):
        mock_repo = MagicMock()
        mock_auth_repo = MagicMock()
        mock_auth_repo.get_user_id.return_value = 1
        mock_hasher = MagicMock()

        with patch("app.aggregator.feed.get_settings", return_value=MockSettings()):
            aggregator = FeedAggregator(mock_repo, mock_auth_repo, mock_hasher, [])

            aggregator.run()

            mock_repo.create_article.assert_not_called()
            mock_repo.find_newspaper_by_title.assert_not_called()

    def test_run_with_empty_scraper(self):
        mock_repo = MagicMock()
        mock_repo.find_newspaper_by_title.return_value = {"id": 1, "title": "Test"}
        mock_auth_repo = MagicMock()
        mock_auth_repo.get_user_id.return_value = 1
        mock_hasher = MagicMock()

        scraper = MockScraper("Empty Paper", articles=[])

        with patch("app.aggregator.feed.get_settings", return_value=MockSettings()):
            aggregator = FeedAggregator(mock_repo, mock_auth_repo, mock_hasher, [scraper])

            aggregator.run()

            mock_repo.create_article.assert_not_called()
