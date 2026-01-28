from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import requests

from app.aggregator.feed import ScrapedArticle


class NewsAPIScraper:
    """Scrape articles from NewsAPI and expose them as `ScrapedArticle` items."""

    _endpoint = "https://newsapi.org/v2/top-headlines"

    def __init__(
        self,
        api_key: str,
        query: str | None = None,
        country: str | None = None,
        category: str | None = None,
        page_size: int = 20,
        session: requests.Session | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("NewsAPI API key must be provided")
        self._api_key = api_key.strip()
        self._query = (query or "").strip() or None
        self._country = (country or "").strip() or None
        self._category = (category or "").strip() or None
        self._page_size = max(1, min(page_size, 100))
        self._session = session or self._build_session()
        self._newspaper_title = self._build_title()
        self._newspaper_description = self._build_description()

    @property
    def newspaper_title(self) -> str:
        return self._newspaper_title

    @property
    def newspaper_description(self) -> str | None:
        return self._newspaper_description

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "CringeBoard-Aggregator/1.0 (+https://example.com)",
            }
        )
        return session

    def _build_title(self) -> str:
        parts = []
        if self._category:
            parts.append(self._category.title())
        if self._query:
            parts.append(f'"{self._query}"')
        if not parts and self._country:
            parts.append(self._country.upper())
        label = " / ".join(parts) if parts else "Top headlines"
        return f"NewsAPI ({label})"

    def _build_description(self) -> str:
        details = []
        if self._country:
            details.append(f"country={self._country}")
        if self._category:
            details.append(f"category={self._category}")
        if self._query:
            details.append(f"query={self._query}")
        return f"NewsAPI feed ({', '.join(details)})" if details else "NewsAPI top headlines feed"

    def scrape(self) -> Iterable[ScrapedArticle]:
        def fetch(include_query: bool) -> list[dict[str, Any]]:
            params: dict[str, Any] = {
                "apiKey": self._api_key,
                "pageSize": self._page_size,
            }
            if include_query and self._query:
                params["q"] = self._query
            if self._country:
                params["country"] = self._country
            if self._category:
                params["category"] = self._category

            response = self._session.get(self._endpoint, params=params, timeout=20)
            response.raise_for_status()
            payload = response.json()
            return payload.get("articles") or []

        articles = fetch(include_query=True)
        if not articles and self._query:
            # Fallback without query to still hydrate the feed when the query is too restrictive.
            articles = fetch(include_query=False)
        for item in articles:
            url = (item.get("url") or "").strip()
            if not url:
                continue
            title = (item.get("title") or "").strip() or "Untitled"
            description = (item.get("description") or item.get("content") or "").strip() or None
            yield ScrapedArticle(
                title=title,
                url=url,
                summary=description,
            )
