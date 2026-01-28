from .base import BaseRSSScraper
from .flipboard import FlipboardAccountScraper, FlipboardMagazineScraper
from .hn import HackerNewsScraper
from .newsapi import NewsAPIScraper
from .wired import WiredScraper

__all__ = [
    "BaseRSSScraper",
    "FlipboardAccountScraper",
    "FlipboardMagazineScraper",
    "HackerNewsScraper",
    "NewsAPIScraper",
    "WiredScraper",
]
