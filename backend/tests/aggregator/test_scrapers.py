from __future__ import annotations

import os
import psycopg

os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost/test-db")


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

from app.aggregator.scrapers.flipboard import FlipboardMagazineScraper


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
