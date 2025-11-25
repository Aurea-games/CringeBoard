from __future__ import annotations

from collections.abc import Iterable
from urllib.parse import urlsplit
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
        atom_feed = False
        items = root.findall(".//item")
        if not items:
            items = root.findall(".//{*}item")
        if not items:
            atom_feed = True
            items = root.findall(".//entry")
            if not items:
                items = root.findall(".//{*}entry")
        for item in items:
            if atom_feed:
                link = self._extract_atom_link(item)
                if not link:
                    continue
                link = link.strip()
                title = self._prepare_title(self.get_text(item, "title"), link)
                description = self.get_text(item, "content") or self.get_text(item, "summary")
            else:
                link = self.get_text(item, "link")
                if not link:
                    continue
                link = link.strip()
                title = self._prepare_title(self.get_text(item, "title"), link)
                description = self.get_text(item, "description") or self.get_text(item, "summary")
            summary = self._build_summary(description, link)
            yield ScrapedArticle(
                title=title,
                url=link,
                summary=summary,
            )

    @staticmethod
    def get_text(a_item: ET.Element, a_tag: str) -> str | None:
        element = a_item.find(a_tag)
        if element is None:
            element = a_item.find(f".//{{*}}{a_tag}")
        if element is None:
            return None
        text = "".join(element.itertext())
        text = text.strip()
        return text if text else None

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

    def _prepare_title(self, raw_title: str | None, link: str) -> str:
        title = (raw_title or "").strip()
        if title:
            if not self._looks_like_url(title):
                return title
            title_from_link = self._derive_title_from_link(link)
            if title_from_link:
                return title_from_link
            return title
        return self._derive_title_from_link(link) or "Untitled"

    def _build_summary(self, raw_description: str | None, link: str) -> str | None:
        if not raw_description:
            return None
        summary = self.clean_html(raw_description)
        if not summary:
            return None
        if self._looks_like_url(summary) and self._urls_match(summary, link):
            return None
        if self._looks_like_metadata_block(summary):
            return None
        return summary

    @staticmethod
    def _looks_like_url(value: str) -> bool:
        candidate = value.strip().lower()
        return candidate.startswith("http://") or candidate.startswith("https://")

    def _urls_match(self, first: str, second: str) -> bool:
        return self._normalize_url(first) == self._normalize_url(second)

    @staticmethod
    def _normalize_url(value: str) -> str:
        candidate = value.strip()
        if not candidate:
            return ""
        try:
            parsed = urlsplit(candidate)
        except ValueError:
            return candidate.rstrip("/")
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        base = netloc or ""
        path = parsed.path.rstrip("/")
        query = f"?{parsed.query}" if parsed.query else ""
        fragment = f"#{parsed.fragment}" if parsed.fragment else ""
        if not base:
            return candidate.rstrip("/")
        return f"{parsed.scheme.lower()}://{base}{path}{query}{fragment}".rstrip("/")

    @staticmethod
    def _derive_title_from_link(link: str) -> str | None:
        try:
            parsed = urlsplit(link.strip())
        except ValueError:
            return None
        netloc = parsed.netloc or ""
        if netloc.startswith("www."):
            netloc = netloc[4:]
        path_segments = [segment for segment in parsed.path.split("/") if segment]
        readable_segment = path_segments[-1] if path_segments else ""
        if readable_segment:
            cleaned = " ".join(part for part in readable_segment.replace("-", " ").replace("_", " ").split())
            if cleaned:
                readable_segment = cleaned
            readable_segment = " ".join(chunk.capitalize() for chunk in readable_segment.split()) or readable_segment
            if netloc:
                return f"{readable_segment} ({netloc})".strip()
            return readable_segment or None
        fallback = parsed.path.strip("/") or netloc
        return fallback or None

    @staticmethod
    def _looks_like_metadata_block(summary: str) -> bool:
        """Detect feed descriptions that repeat metadata, such as HN RSS items."""
        metadata_markers = ("Article URL:", "Comments URL:", "Points:", "# Comments:")
        lines = [line.strip() for line in summary.splitlines() if line.strip()]
        if len(lines) >= 3:
            matches = sum(1 for line in lines if line.startswith(metadata_markers))
            if matches >= 3:
                return True
        flattened = summary.replace("\n", " ").lower()
        matches = sum(1 for marker in metadata_markers if marker.lower() in flattened)
        return matches >= 3

    def _extract_atom_link(self, entry: ET.Element) -> str | None:
        candidates = entry.findall("link")
        if not candidates:
            candidates = entry.findall(".//{*}link")
        preferred = None
        for element in candidates:
            href = element.attrib.get("href")
            if not href:
                continue
            rel = element.attrib.get("rel", "alternate")
            if rel == "alternate":
                return href
            if preferred is None:
                preferred = href
        return preferred
