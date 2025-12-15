from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class NewspaperBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)


class NewspaperCreate(NewspaperBase):
    pass


class NewspaperUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)


class Newspaper(BaseModel):
    id: int
    title: str
    description: str | None
    owner_id: int
    is_public: bool = False
    public_token: str | None = None
    public_url: str | None = None
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
