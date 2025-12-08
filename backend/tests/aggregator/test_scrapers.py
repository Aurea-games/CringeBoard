from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost/test-db")

import psycopg
from app.aggregator.scrapers.base import BaseRSSScraper
from app.aggregator.scrapers.flipboard import FlipboardAccountScraper, FlipboardMagazineScraper


class DummyCursor:
    def __enter__(self) -> DummyCursor:
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
    def __enter__(self) -> DummyConnection:
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


class DummyResponse:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:  # pragma: no cover - no error path in dummy
        return None


class DummySession:
    def __init__(self, payload: str) -> None:
        self._payload = payload
        self.requested_url: str | None = None
        self.timeout: float | None = None

    def get(self, url: str, timeout: float) -> DummyResponse:
        self.requested_url = url
        self.timeout = timeout
        return DummyResponse(self._payload)


SampleFlipboardFeed = """
<rss version="2.0">
  <channel>
    <title>Flipboard Sample</title>
    <item>
      <title>Example Story</title>
      <link>https://flipboard.example/story-1</link>
      <description><![CDATA[<p>First paragraph.</p><p>Second paragraph.</p>]]></description>
    </item>
  </channel>
</rss>
""".strip()


SampleUrlSummaryFeed = """
<rss version="2.0">
  <channel>
    <item>
      <title>https://example.org/story-title</title>
      <link>https://example.org/story-title</link>
      <description>https://example.org/story-title</description>
    </item>
  </channel>
</rss>
""".strip()


SampleHackerNewsFeed = """
<rss version="2.0">
  <channel>
    <item>
      <title>Interesting Story</title>
      <link>https://example.org/story</link>
      <description><![CDATA[
        Article URL: https://example.org/story
        Comments URL: https://news.ycombinator.com/item?id=123
        Points: 100
        # Comments: 42
      ]]></description>
    </item>
  </channel>
</rss>
""".strip()


SampleFlipboardAtomFeed = """
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Flipboard Sample</title>
  <entry>
    <title>Atom Style Story</title>
    <link rel="alternate" href="https://flipboard.example/story-atom" />
    <summary type="html"><![CDATA[<p>Atom summary.</p>]]></summary>
  </entry>
</feed>
""".strip()


def test_flipboard_scraper_parses_rss_feed() -> None:
    session = DummySession(SampleFlipboardFeed)
    scraper = FlipboardMagazineScraper("tech/awesome", a_session=session)

    articles = list(scraper.scrape())

    assert session.requested_url == "https://flipboard.com/@tech/awesome.rss"
    assert session.timeout == 15
    assert len(articles) == 1
    article = articles[0]
    assert article.title == "Example Story"
    assert article.url == "https://flipboard.example/story-1"
    assert article.summary == "First paragraph.\nSecond paragraph."


def test_flipboard_scraper_accepts_full_urls() -> None:
    session = DummySession(SampleFlipboardFeed)
    scraper = FlipboardMagazineScraper("https://flipboard.com/@tech/awesome?from=share", a_session=session)

    list(scraper.scrape())

    assert session.requested_url == "https://flipboard.com/@tech/awesome.rss"
    assert scraper.newspaper_title == "Flipboard / @tech/awesome"


def test_flipboard_scraper_sets_browser_like_headers() -> None:
    scraper = FlipboardMagazineScraper("tech/awesome")

    headers = scraper._session.headers  # type: ignore[attr-defined]
    assert "User-Agent" in headers
    assert "Chrome" in headers["User-Agent"]
    assert headers.get("Accept") and "application/rss+xml" in headers["Accept"]


def test_flipboard_account_scraper_targets_profile_feed() -> None:
    session = DummySession(SampleFlipboardFeed)
    scraper = FlipboardAccountScraper("https://flipboard.com/@TechNews/highlights?from=share", a_session=session)

    list(scraper.scrape())

    assert session.requested_url == "https://flipboard.com/@TechNews.rss"
    assert scraper.newspaper_title == "Flipboard Account / @TechNews"


def test_base_scraper_discards_url_only_summaries() -> None:
    scraper = BaseRSSScraper(
        a_feed_url="https://example.org/feed",
        a_newspaper_title="Example Feed",
    )

    articles = list(scraper.parse_feed(SampleUrlSummaryFeed))

    assert len(articles) == 1
    article = articles[0]
    assert article.url == "https://example.org/story-title"
    assert article.summary is None
    assert article.title == "Story Title (example.org)"


def test_base_scraper_discards_hacker_news_metadata_blocks() -> None:
    scraper = BaseRSSScraper(
        a_feed_url="https://hnrss.org/frontpage",
        a_newspaper_title="Hacker News",
    )

    articles = list(scraper.parse_feed(SampleHackerNewsFeed))

    assert len(articles) == 1
    article = articles[0]
    assert article.url == "https://example.org/story"
    assert article.summary is None
    assert article.title == "Interesting Story"


def test_base_scraper_handles_atom_feed_items() -> None:
    scraper = BaseRSSScraper(
        a_feed_url="https://flipboard.com/@tech/awesome.rss",
        a_newspaper_title="Flipboard Sample",
    )

    articles = list(scraper.parse_feed(SampleFlipboardAtomFeed))

    assert len(articles) == 1
    article = articles[0]
    assert article.url == "https://flipboard.example/story-atom"
    assert article.summary == "Atom summary."
    assert article.title == "Atom Style Story"
