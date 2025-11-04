from __future__ import annotations

from app.aggregator.scrapers.base import BaseRSSScraper


class FlipboardMagazineScraper(BaseRSSScraper):
    """Scraper tailored for Flipboard magazine feeds."""

    def __init__(
        self,
        a_magazine_identifier: str,
        a_session=None,
    ) -> None:
        feed_url = f"https://flipboard.com/@{a_magazine_identifier}.rss"
        title = f"Flipboard / @{a_magazine_identifier}"
        description = f"Flipboard magazine feed for @{a_magazine_identifier}"
        super().__init__(
            a_feed_url=feed_url,
            a_newspaper_title=title,
            a_newspaper_description=description,
            a_session=a_session,
        )
