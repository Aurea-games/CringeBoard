from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from xml.etree import ElementTree as ET

import requests

from app.aggregator.feed import ScrapedArticle


class BaseRSSScraper(ABC):
    """Generic RSS scraper that transforms feed items into `ScrapedArticle` objects."""

    def __init__(
        self,
        feed_url: str,
        newspaper_title: str,
        newspaper_description: str | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self._feed_url = feed_url
        self._newspaper_title = newspaper_title
        self._newspaper_description = newspaper_description
        self._session = session or requests.Session()

    @property
    def newspaper_title(self) -> str:
        return self._newspaper_title

    @property
    def newspaper_description(self) -> str | None:
        return self._newspaper_description

    def scrape(self) -> Iterable[ScrapedArticle]:
        response = self._session.get(self._feed_url, timeout=15)
        response.raise_for_status()
        raw_text = response.text
        return self._parse_feed(raw_text)

    def _parse_feed(self, data: str) -> Iterable[ScrapedArticle]:
        root = ET.fromstring(data)
        channel = root.find("channel")
        items = channel.findall("item") if channel is not None else root.findall(".//item")
        for item in items:
            title = self._get_text(item, "title") or "Untitled"
            link = self._get_text(item, "link")
            if not link:
                continue
            description = self._get_text(item, "description") or self._get_text(item, "summary")
            yield ScrapedArticle(
                title=title.strip(),
                url=link.strip(),
                summary=self._clean_html(description) if description else None,
            )

    @staticmethod
    def _get_text(item: ET.Element, tag: str) -> str | None:
        element = item.find(tag)
        if element is None or element.text is None:
            return None
        return element.text

    @staticmethod
    def _clean_html(raw: str) -> str:
        try:
            from html import unescape
            from re import sub
        except ImportError:
            return raw

        text = unescape(raw)
        text = sub(r"<br\\s*/?>", "\n", text)
        text = sub(r"</p>\s*<p>", "\n", text)
        text = sub(r"<[^>]+>", "", text)
        return text.strip()
