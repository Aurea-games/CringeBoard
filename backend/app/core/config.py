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
    rss_feeds: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "cors_origins", tuple(self.cors_origins or ()))
        object.__setattr__(self, "flipboard_magazines", tuple(self.flipboard_magazines or ()))
        object.__setattr__(self, "rss_feeds", tuple(self.rss_feeds or ()))


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings sourced from environment variables."""
    cors_origins = _parse_origins(os.getenv("CORS_ORIGINS", "http://localhost:3000"))
    flipboard_magazines = _parse_origins(os.getenv("FLIPBOARD_MAGAZINES", "tech/tech"))
    rss_feeds = _parse_origins(
        os.getenv(
            "RSS_FEEDS",
            "https://hnrss.org/frontpage,https://www.wired.com/feed/rss",
        )
    )

    return Settings(
        project_name=os.getenv("PROJECT_NAME", "CringeBoard API"),
        cors_origins=tuple(cors_origins),
        scheduler_interval=int(os.getenv("SCHEDULER_INTERVAL", "60")),
        aggregator_user_email=os.getenv("AGGREGATOR_USER_EMAIL", "aggregator@cringeboard.local"),
        aggregator_user_password=os.getenv("AGGREGATOR_USER_PASSWORD", "change-me"),
        flipboard_magazines=tuple(flipboard_magazines),
        rss_feeds=tuple(rss_feeds),
    )


__all__ = ["Settings", "get_settings"]
