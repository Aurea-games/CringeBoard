from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class NewspaperBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)


class NewspaperCreate(NewspaperBase):
    source_id: int | None = Field(None, ge=1)


class NewspaperUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    source_id: int | None = Field(None, ge=1)


class Newspaper(BaseModel):
    id: int
    title: str
    description: str | None
    owner_id: int
    is_public: bool = False
    public_token: str | None = None
    public_url: str | None = None
    source_id: int | None = None
    created_at: datetime
    updated_at: datetime


class ArticleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str | None = Field(None, max_length=20000)
    url: str | None = Field(None, max_length=2000)


class ArticleUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    content: str | None = Field(None, max_length=20000)
    url: str | None = Field(None, max_length=2000)


class Article(BaseModel):
    id: int
    title: str
    content: str | None
    url: str | None
    owner_id: int
    popularity: int = 0
    created_at: datetime
    updated_at: datetime
    newspaper_ids: list[int] = Field(default_factory=list)


class NewspaperDetail(Newspaper):
    articles: list[Article] = Field(default_factory=list)

    @classmethod
    def from_parts(cls, newspaper_data: dict[str, Any], articles: list[dict[str, Any]]) -> NewspaperDetail:
        base = Newspaper.model_validate(newspaper_data)
        article_models = [Article.model_validate(article) for article in articles]
        return cls(**base.model_dump(), articles=article_models)


class NewspaperShareRequest(BaseModel):
    public: bool


class SourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    feed_url: str | None = Field(None, max_length=2000)
    description: str | None = Field(None, max_length=2000)
    status: str | None = Field(None, min_length=1, max_length=50)


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    feed_url: str | None = Field(None, max_length=2000)
    description: str | None = Field(None, max_length=2000)
    status: str | None = Field(None, min_length=1, max_length=50)


class Source(BaseModel):
    id: int
    name: str
    feed_url: str | None = None
    description: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    is_followed: bool = False


class Notification(BaseModel):
    id: int
    user_id: int
    source_id: int
    article_id: int | None = None
    newspaper_id: int | None = None
    message: str
    is_read: bool = False
    created_at: datetime


class CustomFeedFilterRules(BaseModel):
    include_sources: list[int] = Field(default_factory=list)
    exclude_sources: list[int] = Field(default_factory=list)
    include_newspapers: list[int] = Field(default_factory=list)
    include_keywords: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)
    min_popularity: int | None = Field(None, ge=0)


class CustomFeedCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    filter_rules: CustomFeedFilterRules = Field(default_factory=CustomFeedFilterRules)


class CustomFeedUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    filter_rules: CustomFeedFilterRules | None = None


class CustomFeed(BaseModel):
    id: int
    owner_id: int
    name: str
    description: str | None = None
    filter_rules: CustomFeedFilterRules = Field(default_factory=CustomFeedFilterRules)
    created_at: datetime
    updated_at: datetime


class CustomFeedWithArticles(CustomFeed):
    articles: list[Article] = Field(default_factory=list)

    @classmethod
    def from_parts(cls, feed_data: dict[str, Any], articles: list[dict[str, Any]]) -> CustomFeedWithArticles:
        base = CustomFeed.model_validate(feed_data)
        article_models = [Article.model_validate(article) for article in articles]
        return cls(**base.model_dump(), articles=article_models)
