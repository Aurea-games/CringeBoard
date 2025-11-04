from __future__ import annotations

from app.aggregator.scrapers.base import BaseRSSScraper


class FlipboardMagazineScraper(BaseRSSScraper):
    """Scraper tailored for Flipboard magazine feeds."""

    def __init__(
        self,
        magazine_identifier: str,
        session=None,
    ) -> None:
        feed_url = f"https://flipboard.com/@{magazine_identifier}.rss"
        title = f"Flipboard / @{magazine_identifier}"
        description = f"Flipboard magazine feed for @{magazine_identifier}"
        super().__init__(feed_url, title, description, session=session)
