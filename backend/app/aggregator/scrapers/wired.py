from __future__ import annotations

from app.aggregator.scrapers.base import BaseRSSScraper


class WiredScraper(BaseRSSScraper):
    """Scraper for Wired.com's RSS feed."""

    def __init__(self, session=None) -> None:
        super().__init__(
            feed_url="https://www.wired.com/feed/rss",
            newspaper_title="Wired",
            newspaper_description="The latest technology news from Wired.",
            session=session,
        )
