from __future__ import annotations

from app.aggregator.scrapers.base import BaseRSSScraper


class HackerNewsScraper(BaseRSSScraper):
    """Scrape the Hacker News front page via hnrss."""

    def __init__(self, session=None) -> None:
        super().__init__(
            feed_url="https://hnrss.org/frontpage",
            newspaper_title="Hacker News Front Page",
            newspaper_description="Top stories from Hacker News via hnrss.org.",
            session=session,
        )
