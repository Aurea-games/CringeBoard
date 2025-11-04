from __future__ import annotations

from app.aggregator.scrapers.base import BaseRSSScraper


class WiredScraper(BaseRSSScraper):
    """Scraper for Wired.com's RSS feed."""

    def __init__(self, a_session=None) -> None:
        super().__init__(
            a_feed_url="https://www.wired.com/feed/rss",
            a_newspaper_title="Wired",
            a_newspaper_description="The latest technology news from Wired.",
            a_session=a_session,
        )
