from __future__ import annotations

import requests

from app.aggregator.scrapers.base import BaseRSSScraper


def _normalize_identifier(raw_identifier: str, allow_subpath: bool = True) -> str:
    slug = (raw_identifier or "").strip()
    if not slug:
        raise ValueError("Flipboard identifier must not be empty")

    lowered = slug.lower()
    for prefix in ("https://flipboard.com/", "http://flipboard.com/", "flipboard.com/"):
        if lowered.startswith(prefix):
            slug = slug[len(prefix) :]
            lowered = slug.lower()
            break

    slug = slug.split("?", 1)[0]
    slug = slug.split("#", 1)[0]
    slug = slug.lstrip("@/")
    if not allow_subpath and "/" in slug:
        slug = slug.split("/", 1)[0]
    if slug.endswith(".rss"):
        slug = slug[:-4]
    slug = slug.strip("/")
    if not slug:
        raise ValueError("Flipboard identifier must not be empty")
    return slug


def _build_session(existing_session: requests.Session | None) -> requests.Session:
    if existing_session is not None:
        return existing_session
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )
    return session


class FlipboardMagazineScraper(BaseRSSScraper):
    """Scraper tailored for Flipboard magazine feeds."""

    def __init__(
        self,
        a_magazine_identifier: str,
        a_session=None,
    ) -> None:
        slug = _normalize_identifier(a_magazine_identifier)
        feed_url = f"https://flipboard.com/@{slug}.rss"
        title = f"Flipboard / @{slug}"
        description = f"Flipboard magazine feed for @{slug}"
        session = _build_session(a_session)
        super().__init__(
            a_feed_url=feed_url,
            a_newspaper_title=title,
            a_newspaper_description=description,
            a_session=session,
        )


class FlipboardAccountScraper(BaseRSSScraper):
    """Scraper for the latest stories curated by a Flipboard account."""

    def __init__(self, a_account_identifier: str, a_session=None) -> None:
        username = _normalize_identifier(a_account_identifier, allow_subpath=False)
        feed_url = f"https://flipboard.com/@{username}.rss"
        title = f"Flipboard Account / @{username}"
        description = f"Latest items curated by @{username} on Flipboard."
        session = _build_session(a_session)
        super().__init__(
            a_feed_url=feed_url,
            a_newspaper_title=title,
            a_newspaper_description=description,
            a_session=session,
        )
