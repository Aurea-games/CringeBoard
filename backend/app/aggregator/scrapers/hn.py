from __future__ import annotations

from app.aggregator.scrapers.base import BaseRSSScraper


class HackerNewsScraper(BaseRSSScraper):
    """Scrape the Hacker News front page via hnrss."""

    def __init__(self, a_session=None) -> None:
        super().__init__(
            a_feed_url="https://hnrss.org/frontpage",
            a_newspaper_title="Hacker News Front Page",
            a_newspaper_description="Top stories from Hacker News via hnrss.org.",
            a_session=a_session,
        )
