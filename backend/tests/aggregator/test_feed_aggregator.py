from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost/test-db")

import psycopg
from collections.abc import Iterable


class DummyCursor:
    def __enter__(self) -> "DummyCursor":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False

    def execute(self, *args, **kwargs) -> None:  # pragma: no cover - simple stub
        return None

    def fetchone(self):
        return None

    def fetchall(self):
        return []


class DummyConnection:
    def __enter__(self) -> "DummyConnection":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False

    def cursor(self) -> DummyCursor:
        return DummyCursor()

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None

    def close(self) -> None:
        return None


def fake_connect(*args, **kwargs) -> DummyConnection:
    return DummyConnection()


psycopg.connect = fake_connect  # type: ignore[assignment]

import pytest

from app.aggregator.feed import FeedAggregator, ScrapedArticle
from tests.conftest import InMemoryAggregatorRepository, InMemoryAuthRepository, SimplePasswordHasher


class DummyScraper:
    def __init__(self, title: str, description: str | None, articles: Iterable[ScrapedArticle]):
        self._title = title
        self._description = description
        self._articles = list(articles)

    @property
    def newspaper_title(self) -> str:
        return self._title

    @property
    def newspaper_description(self) -> str | None:
        return self._description

    def scrape(self) -> Iterable[ScrapedArticle]:
        return list(self._articles)


def test_feed_aggregator_persists_articles(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core import config

    monkeypatch.setenv("AGGREGATOR_USER_EMAIL", "feeds@example.org")
    monkeypatch.setenv("AGGREGATOR_USER_PASSWORD", "super-secret")
    config.get_settings.cache_clear()

    aggregator_repository = InMemoryAggregatorRepository()
    auth_repository = InMemoryAuthRepository()
    password_hasher = SimplePasswordHasher()

    scraper_one = DummyScraper(
        title="Tech Daily",
        description="Daily tech highlights",
        articles=[
            ScrapedArticle(title="Story A", url="https://example.org/story-a", summary="Summary A"),
            ScrapedArticle(title="Story B", url="https://example.org/story-b", summary="Summary B"),
        ],
    )
    scraper_two = DummyScraper(
        title="Flipboard / @tech",
        description="Flipboard tech magazine",
        articles=[
            ScrapedArticle(title="Story A", url="https://example.org/story-a", summary="Extra context"),
            ScrapedArticle(title="Story C", url="https://example.org/story-c", summary=None),
        ],
    )

    aggregator = FeedAggregator(
        repository=aggregator_repository,
        auth_repository=auth_repository,
        password_hasher=password_hasher,
        scrapers=[scraper_one, scraper_two],
    )

    aggregator.run()

    owner_id = auth_repository.get_user_id("feeds@example.org")
    assert owner_id is not None

    newspapers = aggregator_repository.list_newspapers()
    assert {paper["title"] for paper in newspapers} == {"Tech Daily", "Flipboard / @tech"}

    # Story A should be attached to both newspapers, while Story B and C remain single-source.
    tech_daily = aggregator_repository.find_newspaper_by_title(owner_id, "Tech Daily")
    flipboard = aggregator_repository.find_newspaper_by_title(owner_id, "Flipboard / @tech")
    assert tech_daily is not None
    assert flipboard is not None

    articles_tech = aggregator_repository.list_articles_for_newspaper(tech_daily["id"])
    articles_flip = aggregator_repository.list_articles_for_newspaper(flipboard["id"])

    urls_tech = {article["url"] for article in articles_tech}
    urls_flip = {article["url"] for article in articles_flip}

    assert urls_tech == {"https://example.org/story-a", "https://example.org/story-b"}
    assert urls_flip == {"https://example.org/story-a", "https://example.org/story-c"}

    shared_article = aggregator_repository.find_article_by_url("https://example.org/story-a")
    assert shared_article is not None
    assert sorted(shared_article["newspaper_ids"]) == sorted([tech_daily["id"], flipboard["id"]])
