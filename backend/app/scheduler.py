from __future__ import annotations

import time

from app.aggregator.feed import FeedAggregator
from app.aggregator.scrapers import BaseRSSScraper, FlipboardMagazineScraper
from app.api.routes.aggregator.repository import AggregatorRepository
from app.api.routes.auth.repository import AuthRepository
from app.api.routes.auth.services import PasswordHasher
from app.core.config import Settings, get_settings


def build_scrapers(a_settings: Settings):
    scrapers = []
    for feed in a_settings.rss_feeds:
        parts = [part.strip() for part in feed.split("|") if part.strip()]
        if not parts:
            continue
        if len(parts) == 1:
            title = parts[0]
            url = parts[0]
            description = None
        elif len(parts) == 2:
            title, url = parts
            description = None
        else:
            title, url, description = parts[0], parts[1], parts[2]
        scrapers.append(
            BaseRSSScraper(
                a_feed_url=url,
                a_newspaper_title=title,
                a_newspaper_description=description,
            )
        )

    for magazine in a_settings.flipboard_magazines:
        if not magazine:
            continue
        scrapers.append(FlipboardMagazineScraper(magazine))
    return scrapers


def main() -> None:
    settings = get_settings()
    scrapers = build_scrapers(settings)
    aggregator = FeedAggregator(
        a_repository=AggregatorRepository(),
        a_auth_repository=AuthRepository(),
        a_password_hasher=PasswordHasher(),
        a_scrapers=scrapers,
    )

    interval = settings.scheduler_interval
    print("Scheduler started. Interval:", interval, "seconds", flush=True)
    while True:
        print("[scheduler] running feed aggregation", flush=True)
        try:
            aggregator.run()
        except Exception as exc:  # pragma: no cover - defensive logging only
            print(f"[scheduler] aggregation failed: {exc}", flush=True)
        time.sleep(interval)


if __name__ == "__main__":
    main()
