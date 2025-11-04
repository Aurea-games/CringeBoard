from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from app.api.routes.aggregator.repository import AggregatorRepository
from app.api.routes.auth.repository import AuthRepository
from app.api.routes.auth.services import PasswordHasher
from app.core.config import get_settings


@dataclass(frozen=True)
class ScrapedArticle:
    title: str
    url: str
    summary: str | None = None


class FeedScraper(Protocol):
    """Simple interface every concrete feed scraper must implement."""

    @property
    def newspaper_title(self) -> str: ...

    @property
    def newspaper_description(self) -> str | None: ...

    def scrape(self) -> Iterable[ScrapedArticle]: ...


class FeedAggregator:
    """Persist articles provided by feed scrapers into the local database."""

    def __init__(
        self,
        a_repository: AggregatorRepository,
        a_auth_repository: AuthRepository,
        a_password_hasher: PasswordHasher,
        a_scrapers: Iterable[FeedScraper],
    ) -> None:
        self._repository = a_repository
        self._auth_repository = a_auth_repository
        self._password_hasher = a_password_hasher
        self._scrapers = list(a_scrapers)
        self._settings = get_settings()

    def run(self) -> None:
        owner_id = self.ensure_system_user()
        for scraper in self._scrapers:
            newspaper = self.ensure_newspaper(owner_id, scraper)
            newspaper_id = newspaper["id"]
            for article in scraper.scrape():
                existing = self._repository.find_article_by_url(article.url)
                if existing is None:
                    self._repository.create_article(
                        owner_id=owner_id,
                        newspaper_id=newspaper_id,
                        title=article.title,
                        content=article.summary,
                        url=article.url,
                    )
                else:
                    self._repository.assign_article_to_newspaper(existing["id"], newspaper_id)

    def ensure_system_user(self) -> int:
        email = self._settings.aggregator_user_email
        user_id = self._auth_repository.get_user_id(email)
        if user_id is not None:
            return user_id

        password_hash = self._password_hasher.hash(self._settings.aggregator_user_password)
        return self._auth_repository.create_user(email, password_hash)

    def ensure_newspaper(self, a_owner_id: int, a_scraper: FeedScraper) -> dict[str, object]:
        existing = self._repository.find_newspaper_by_title(a_owner_id, a_scraper.newspaper_title)
        if existing is not None:
            return existing
        return self._repository.create_newspaper(
            owner_id=a_owner_id,
            title=a_scraper.newspaper_title,
            description=a_scraper.newspaper_description,
        )
