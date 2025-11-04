from __future__ import annotations

from collections.abc import Iterable
from xml.etree import ElementTree as ET

import requests

from app.aggregator.feed import ScrapedArticle


class BaseRSSScraper:
    """Generic RSS scraper that transforms feed items into `ScrapedArticle` objects."""

    def __init__(
        self,
        a_feed_url: str,
        a_newspaper_title: str,
        a_newspaper_description: str | None = None,
        a_session: requests.Session | None = None,
    ) -> None:
        self._feed_url = a_feed_url
        self._newspaper_title = a_newspaper_title
        self._newspaper_description = a_newspaper_description
        self._session = a_session or requests.Session()

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
        return self.parse_feed(raw_text)

    def parse_feed(self, a_data: str) -> Iterable[ScrapedArticle]:
        root = ET.fromstring(a_data)
        channel = root.find("channel")
        items = channel.findall("item") if channel is not None else root.findall(".//item")
        for item in items:
            title = self.get_text(item, "title") or "Untitled"
            link = self.get_text(item, "link")
            if not link:
                continue
            description = self.get_text(item, "description") or self.get_text(item, "summary")
            yield ScrapedArticle(
                title=title.strip(),
                url=link.strip(),
                summary=self.clean_html(description) if description else None,
            )

    @staticmethod
    def get_text(a_item: ET.Element, a_tag: str) -> str | None:
        element = a_item.find(a_tag)
        if element is None or element.text is None:
            return None
        return element.text

    @staticmethod
    def clean_html(a_raw: str) -> str:
        try:
            from html import unescape
            from re import sub
        except ImportError:
            return a_raw

        text = unescape(a_raw)
        text = sub(r"<br\\s*/?>", "\n", text)
        text = sub(r"</p>\s*<p>", "\n", text)
        text = sub(r"<[^>]+>", "", text)
        return text.strip()
