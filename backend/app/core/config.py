from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _parse_origins(raw_value: str) -> list[str]:
    """Split a comma-separated list of origins while trimming whitespace."""
    return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    project_name: str = "CringeBoard API"
    cors_origins: tuple[str, ...] = ()
    scheduler_interval: int = 60
    aggregator_user_email: str = "aggregator@cringeboard.local"
    aggregator_user_password: str = "change-me"
    flipboard_magazines: tuple[str, ...] = ()
    flipboard_accounts: tuple[str, ...] = ()
    rss_feeds: tuple[str, ...] = ()
    newsapi_key: str | None = None
    newsapi_query: str | None = None
    newsapi_country: str | None = None
    newsapi_category: str | None = None
    newsapi_page_size: int = 20

    def __post_init__(self) -> None:
        object.__setattr__(self, "cors_origins", tuple(self.cors_origins or ()))
        object.__setattr__(self, "flipboard_magazines", tuple(self.flipboard_magazines or ()))
        object.__setattr__(self, "flipboard_accounts", tuple(self.flipboard_accounts or ()))
        object.__setattr__(self, "rss_feeds", tuple(self.rss_feeds or ()))


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings sourced from environment variables."""
    cors_origins = _parse_origins(os.getenv("CORS_ORIGINS", "http://localhost:3000"))
    flipboard_magazines = _parse_origins(os.getenv("FLIPBOARD_MAGAZINES", "tech/tech"))
    flipboard_accounts = _parse_origins(os.getenv("FLIPBOARD_ACCOUNTS", ""))
    rss_feeds = _parse_origins(
        os.getenv(
            "RSS_FEEDS",
            "https://hnrss.org/frontpage,https://www.wired.com/feed/rss",
        )
    )
    newsapi_key = os.getenv("NEWSAPI_KEY") or None
    newsapi_query = os.getenv("NEWSAPI_QUERY") or None
    newsapi_country = os.getenv("NEWSAPI_COUNTRY") or None
    newsapi_category = os.getenv("NEWSAPI_CATEGORY") or None
    newsapi_page_size = int(os.getenv("NEWSAPI_PAGE_SIZE", "20"))

    return Settings(
        project_name=os.getenv("PROJECT_NAME", "CringeBoard API"),
        cors_origins=tuple(cors_origins),
        scheduler_interval=int(os.getenv("SCHEDULER_INTERVAL", "60")),
        aggregator_user_email=os.getenv("AGGREGATOR_USER_EMAIL", "aggregator@cringeboard.local"),
        aggregator_user_password=os.getenv("AGGREGATOR_USER_PASSWORD", "change-me"),
        flipboard_magazines=tuple(flipboard_magazines),
        flipboard_accounts=tuple(flipboard_accounts),
        rss_feeds=tuple(rss_feeds),
        newsapi_key=newsapi_key,
        newsapi_query=newsapi_query,
        newsapi_country=newsapi_country,
        newsapi_category=newsapi_category,
        newsapi_page_size=newsapi_page_size,
    )


__all__ = ["Settings", "get_settings"]
