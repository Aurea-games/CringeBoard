from __future__ import annotations

import secrets
from typing import Any

from fastapi import HTTPException, status

from app.api.routes.auth.repository import AuthRepository
from app.api.routes.auth.validators import normalize_email

from . import schemas
from .repository import AggregatorRepository


class AggregatorService:
    """Business logic for managing newspapers and articles."""

    _NEWSPAPER_NOT_FOUND = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Newspaper not found.",
    )
    _ARTICLE_NOT_FOUND = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Article not found.",
    )
    _SOURCE_NOT_FOUND = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Source not found.",
    )
    _NOTIFICATION_NOT_FOUND = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Notification not found.",
    )

    def __init__(self, repository: AggregatorRepository, auth_repository: AuthRepository) -> None:
        self._repository = repository
        self._auth_repository = auth_repository

    def list_newspapers(self, search: str | None = None, owner_email: str | None = None) -> list[schemas.Newspaper]:
        owner_id: int | None = None
        if owner_email:
            normalized = normalize_email(owner_email)
            owner_id = self._auth_repository.get_user_id(normalized)
            if owner_id is None:
                return []

        rows = self._repository.search_newspapers(search, owner_id)
        return [self._to_newspaper_model(row) for row in rows]

    def create_newspaper(self, owner_email: str, payload: schemas.NewspaperCreate) -> schemas.Newspaper:
        owner_id = self.get_user_id(owner_email)
        title = payload.title.strip()
        if not title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Title must not be empty.",
            )
        description = payload.description.strip() if payload.description else None
        if description == "":
            description = None
        source_id = payload.source_id
        source = None
        if source_id is not None:
            source = self._repository.get_source(source_id)
            if source is None:
                raise self._SOURCE_NOT_FOUND
        record = self._repository.create_newspaper(owner_id, title, description, source_id=source_id)
        newspaper = self._to_newspaper_model(record)
        if source:
            self._notify_newspaper_followers(source, newspaper)
        return newspaper

    def get_newspaper(self, newspaper_id: int) -> schemas.NewspaperDetail:
        record = self._repository.get_newspaper(newspaper_id)
        if record is None:
            raise self._NEWSPAPER_NOT_FOUND
        articles = self._repository.search_articles(newspaper_id=newspaper_id)
        return schemas.NewspaperDetail.from_parts(self._inject_public_url(record), articles)

    def update_newspaper(
        self,
        newspaper_id: int,
        owner_email: str,
        payload: schemas.NewspaperUpdate,
    ) -> schemas.Newspaper:
        owner_id = self.get_user_id(owner_email)
        current = self._repository.get_newspaper(newspaper_id)
        if current is None:
            raise self._NEWSPAPER_NOT_FOUND
        self.ensure_ownership(current["owner_id"], owner_id, "modify this newspaper")

        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one field must be provided for update.",
            )

        title = updates.get("title")
        description = updates.get("description")
        if isinstance(title, str):
            title = title.strip()
            if not title:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Title must not be empty.",
                )
        if isinstance(description, str):
            description = description.strip()
            if not description:
                description = None
        update_source_id = "source_id" in updates
        source_id = updates.get("source_id") if update_source_id else None
        if update_source_id and source_id is not None and self._repository.get_source(source_id) is None:
            raise self._SOURCE_NOT_FOUND
        record = self._repository.update_newspaper(
            newspaper_id,
            title,
            description,
            source_id,
            update_source_id=update_source_id,
        )
        if record is None:
            raise self._NEWSPAPER_NOT_FOUND
        return self._to_newspaper_model(record)

    def delete_newspaper(self, newspaper_id: int, owner_email: str) -> None:
        owner_id = self.get_user_id(owner_email)
        current = self._repository.get_newspaper(newspaper_id)
        if current is None:
            raise self._NEWSPAPER_NOT_FOUND
        self.ensure_ownership(current["owner_id"], owner_id, "delete this newspaper")

        if not self._repository.delete_newspaper(newspaper_id):
            raise self._NEWSPAPER_NOT_FOUND

    def list_articles_for_newspaper(self, newspaper_id: int, search: str | None = None) -> list[schemas.Article]:
        # Raises if the newspaper does not exist to ensure clients receive a 404.
        if self._repository.get_newspaper(newspaper_id) is None:
            raise self._NEWSPAPER_NOT_FOUND
        rows = self._repository.search_articles(search=search, newspaper_id=newspaper_id)
        return [schemas.Article.model_validate(row) for row in rows]

    def search_articles(
        self,
        search: str | None = None,
        owner_email: str | None = None,
        newspaper_id: int | None = None,
        order_by_popularity: bool = False,
    ) -> list[schemas.Article]:
        owner_id: int | None = None
        if owner_email:
            normalized = normalize_email(owner_email)
            owner_id = self._auth_repository.get_user_id(normalized)
            if owner_id is None:
                return []

        rows = self._repository.search_articles(
            search=search,
            owner_id=owner_id,
            newspaper_id=newspaper_id,
            order_by_popularity=order_by_popularity,
        )
        return [schemas.Article.model_validate(row) for row in rows]

    def create_article(
        self,
        newspaper_id: int,
        owner_email: str,
        payload: schemas.ArticleCreate,
    ) -> schemas.Article:
        owner_id = self.get_user_id(owner_email)
        newspaper = self._repository.get_newspaper(newspaper_id)
        if newspaper is None:
            raise self._NEWSPAPER_NOT_FOUND
        self.ensure_ownership(newspaper["owner_id"], owner_id, "add articles to this newspaper")

        article_title = payload.title.strip()
        if not article_title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Title must not be empty.",
            )
        url = payload.url.strip() if isinstance(payload.url, str) else None
        if url == "":
            url = None
        content = payload.content.strip() if payload.content else None
        if content == "":
            content = None
        record = self._repository.create_article(
            owner_id=owner_id,
            newspaper_id=newspaper_id,
            title=article_title,
            content=content,
            url=url,
        )
        article = schemas.Article.model_validate(record)
        self._maybe_notify_new_article(newspaper, article)
        return article

    def attach_article_to_newspaper(
        self,
        newspaper_id: int,
        article_id: int,
        owner_email: str,
    ) -> schemas.Article:
        owner_id = self.get_user_id(owner_email)
        newspaper = self._repository.get_newspaper(newspaper_id)
        if newspaper is None:
            raise self._NEWSPAPER_NOT_FOUND
        self.ensure_ownership(newspaper["owner_id"], owner_id, "modify this newspaper")

        article = self._repository.get_article(article_id)
        if article is None:
            raise self._ARTICLE_NOT_FOUND

        record = self._repository.assign_article_to_newspaper(article_id, newspaper_id)
        if record is None:
            raise self._ARTICLE_NOT_FOUND
        attached = schemas.Article.model_validate(record)
        self._maybe_notify_new_article(newspaper, attached)
        return attached

    def detach_article_from_newspaper(
        self,
        newspaper_id: int,
        article_id: int,
        owner_email: str,
    ) -> schemas.Article:
        owner_id = self.get_user_id(owner_email)
        newspaper = self._repository.get_newspaper(newspaper_id)
        if newspaper is None:
            raise self._NEWSPAPER_NOT_FOUND
        self.ensure_ownership(newspaper["owner_id"], owner_id, "modify this newspaper")

        article = self._repository.get_article(article_id)
        if article is None:
            raise self._ARTICLE_NOT_FOUND

        record = self._repository.detach_article_from_newspaper(article_id, newspaper_id)
        if record is None:
            # If article exists but association removal failed, return article not found
            raise self._ARTICLE_NOT_FOUND
        return schemas.Article.model_validate(record)

    def get_article(self, article_id: int) -> schemas.Article:
        record = self._repository.get_article(article_id)
        if record is None:
            raise self._ARTICLE_NOT_FOUND
        return schemas.Article.model_validate(record)

    def list_related_articles(self, article_id: int, limit: int = 10) -> list[schemas.Article]:
        if self._repository.get_article(article_id) is None:
            raise self._ARTICLE_NOT_FOUND
        rows = self._repository.get_related_articles(article_id, limit=limit)
        return [schemas.Article.model_validate(row) for row in rows]

    def share_newspaper(self, newspaper_id: int, owner_email: str, make_public: bool) -> schemas.Newspaper:
        owner_id = self.get_user_id(owner_email)
        newspaper = self._repository.get_newspaper(newspaper_id)
        if newspaper is None:
            raise self._NEWSPAPER_NOT_FOUND
        self.ensure_ownership(newspaper["owner_id"], owner_id, "modify this newspaper")

        public_token: str | None = newspaper.get("public_token")
        if make_public and not public_token:
            public_token = secrets.token_urlsafe(16)
        if not make_public:
            public_token = newspaper.get("public_token")
        updated = self._repository.update_newspaper_publication(
            newspaper_id=newspaper_id,
            is_public=make_public,
            public_token=public_token if make_public else public_token,
        )
        if updated is None:
            raise self._NEWSPAPER_NOT_FOUND
        return self._to_newspaper_model(updated)

    def get_public_newspaper(self, token: str) -> schemas.NewspaperDetail:
        record = self._repository.get_newspaper_by_token(token.strip())
        if record is None:
            raise self._NEWSPAPER_NOT_FOUND
        articles = self._repository.search_articles(newspaper_id=record["id"])
        return schemas.NewspaperDetail.from_parts(self._inject_public_url(record), articles)

    def favorite_article(self, article_id: int, user_email: str) -> schemas.Article:
        user_id = self.get_user_id(user_email)
        article = self._repository.get_article(article_id)
        if article is None:
            raise self._ARTICLE_NOT_FOUND

        record = self._repository.add_article_favorite(user_id, article_id)
        if record is None:
            raise self._ARTICLE_NOT_FOUND
        return schemas.Article.model_validate(record)

    def unfavorite_article(self, article_id: int, user_email: str) -> schemas.Article:
        user_id = self.get_user_id(user_email)
        if self._repository.get_article(article_id) is None:
            raise self._ARTICLE_NOT_FOUND
        record = self._repository.remove_article_favorite(user_id, article_id)
        if record is None:
            raise self._ARTICLE_NOT_FOUND
        return schemas.Article.model_validate(record)

    def list_favorite_articles(self, user_email: str) -> list[schemas.Article]:
        user_id = self.get_user_id(user_email)
        rows = self._repository.list_favorite_articles(user_id)
        return [schemas.Article.model_validate(row) for row in rows]

    def save_article_for_later(self, article_id: int, user_email: str) -> schemas.Article:
        user_id = self.get_user_id(user_email)
        if self._repository.get_article(article_id) is None:
            raise self._ARTICLE_NOT_FOUND
        record = self._repository.add_read_later(user_id, article_id)
        if record is None:
            raise self._ARTICLE_NOT_FOUND
        return schemas.Article.model_validate(record)

    def remove_article_from_read_later(self, article_id: int, user_email: str) -> schemas.Article:
        user_id = self.get_user_id(user_email)
        if self._repository.get_article(article_id) is None:
            raise self._ARTICLE_NOT_FOUND
        record = self._repository.remove_read_later(user_id, article_id)
        if record is None:
            raise self._ARTICLE_NOT_FOUND
        return schemas.Article.model_validate(record)

    def list_read_later_articles(self, user_email: str) -> list[schemas.Article]:
        user_id = self.get_user_id(user_email)
        rows = self._repository.list_read_later_articles(user_id)
        return [schemas.Article.model_validate(row) for row in rows]

    def update_article(
        self,
        article_id: int,
        owner_email: str,
        payload: schemas.ArticleUpdate,
    ) -> schemas.Article:
        owner_id = self.get_user_id(owner_email)
        current = self._repository.get_article(article_id)
        if current is None:
            raise self._ARTICLE_NOT_FOUND
        self.ensure_ownership(current["owner_id"], owner_id, "modify this article")

        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one field must be provided for update.",
            )

        title = updates.get("title")
        if isinstance(title, str):
            title = title.strip()
        content = updates.get("content")
        if isinstance(content, str):
            content = content.strip()
            if not content:
                content = None
        url = updates.get("url")
        if isinstance(url, str):
            url = url.strip()
            if not url:
                url = None

        record = self._repository.update_article(article_id, title, content, url)
        if record is None:
            raise self._ARTICLE_NOT_FOUND
        return schemas.Article.model_validate(record)

    def delete_article(self, article_id: int, owner_email: str) -> None:
        owner_id = self.get_user_id(owner_email)
        current = self._repository.get_article(article_id)
        if current is None:
            raise self._ARTICLE_NOT_FOUND
        self.ensure_ownership(current["owner_id"], owner_id, "delete this article")

        if not self._repository.delete_article(article_id):
            raise self._ARTICLE_NOT_FOUND

    # ---- Sources ----
    def list_sources(
        self,
        search: str | None = None,
        status: str | None = None,
        follower_email: str | None = None,
    ) -> list[schemas.Source]:
        follower_id: int | None = None
        if follower_email:
            follower_id = self._auth_repository.get_user_id(normalize_email(follower_email))
        rows = self._repository.list_sources(search=search, status=status, follower_id=follower_id)
        return [schemas.Source.model_validate(row) for row in rows]

    def create_source(self, payload: schemas.SourceCreate) -> schemas.Source:
        name = payload.name.strip()
        if not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Name must not be empty.",
            )
        feed_url = payload.feed_url.strip() if isinstance(payload.feed_url, str) else None
        if feed_url == "":
            feed_url = None
        description = payload.description.strip() if isinstance(payload.description, str) else None
        if description == "":
            description = None
        status_value = payload.status.strip() if isinstance(payload.status, str) else "active"
        record = self._repository.create_source(
            name=name,
            feed_url=feed_url,
            description=description,
            status=status_value or "active",
        )
        return schemas.Source.model_validate(record)

    def get_source(self, source_id: int, follower_email: str | None = None) -> schemas.Source:
        follower_id: int | None = None
        if follower_email:
            follower_id = self._auth_repository.get_user_id(normalize_email(follower_email))
        record = self._repository.get_source(source_id, follower_id=follower_id)
        if record is None:
            raise self._SOURCE_NOT_FOUND
        return schemas.Source.model_validate(record)

    def update_source(
        self,
        source_id: int,
        payload: schemas.SourceUpdate,
    ) -> schemas.Source:
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one field must be provided for update.",
            )
        name = updates.get("name")
        feed_url = updates.get("feed_url")
        description = updates.get("description")
        status_value = updates.get("status")
        if isinstance(name, str):
            name = name.strip()
            if not name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Name must not be empty.",
                )
        if isinstance(feed_url, str):
            feed_url = feed_url.strip() or None
        if isinstance(description, str):
            description = description.strip() or None
        if isinstance(status_value, str):
            status_value = status_value.strip() or None
        record = self._repository.update_source(
            source_id=source_id,
            name=name,
            feed_url=feed_url,
            description=description,
            status=status_value,
        )
        if record is None:
            raise self._SOURCE_NOT_FOUND
        return schemas.Source.model_validate(record)

    def follow_source(self, source_id: int, user_email: str) -> schemas.Source:
        user_id = self.get_user_id(user_email)
        if self._repository.get_source(source_id) is None:
            raise self._SOURCE_NOT_FOUND
        record = self._repository.follow_source(user_id, source_id)
        if record is None:
            raise self._SOURCE_NOT_FOUND
        return schemas.Source.model_validate(record)

    def unfollow_source(self, source_id: int, user_email: str) -> schemas.Source:
        user_id = self.get_user_id(user_email)
        if self._repository.get_source(source_id) is None:
            raise self._SOURCE_NOT_FOUND
        record = self._repository.unfollow_source(user_id, source_id)
        if record is None:
            raise self._SOURCE_NOT_FOUND
        return schemas.Source.model_validate(record)

    def list_followed_sources(self, user_email: str) -> list[schemas.Source]:
        user_id = self.get_user_id(user_email)
        rows = self._repository.list_followed_sources(user_id)
        return [schemas.Source.model_validate(row) for row in rows]

    # ---- Notifications ----
    def list_notifications(self, user_email: str, include_read: bool = False) -> list[schemas.Notification]:
        user_id = self.get_user_id(user_email)
        rows = self._repository.list_notifications(user_id, include_read=include_read)
        return [schemas.Notification.model_validate(row) for row in rows]

    def mark_notification_read(self, notification_id: int, user_email: str) -> schemas.Notification:
        user_id = self.get_user_id(user_email)
        record = self._repository.mark_notification_read(user_id, notification_id)
        if record is None:
            raise self._NOTIFICATION_NOT_FOUND
        return schemas.Notification.model_validate(record)

    def get_user_id(self, email: str) -> int:
        user_id = self._auth_repository.get_user_id(email)
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        return user_id

    @staticmethod
    def ensure_ownership(resource_owner_id: int, requester_id: int, action: str) -> None:
        if resource_owner_id != requester_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not have permission to {action}.",
            )

    def _maybe_notify_new_article(self, newspaper: dict[str, Any], article: schemas.Article) -> None:
        source = self._get_source_from_newspaper(newspaper)
        if source is None:
            return
        message = self._build_article_notification_message(source["name"], newspaper.get("title"), article.title)
        self._repository.create_notifications_for_source_followers(
            source_id=source["id"],
            article_id=article.id,
            newspaper_id=newspaper.get("id"),
            message=message,
        )

    def _notify_newspaper_followers(self, source: dict[str, Any], newspaper: schemas.Newspaper) -> None:
        message = self._build_newspaper_notification_message(source["name"], newspaper.title)
        self._repository.create_notifications_for_source_followers(
            source_id=source["id"],
            newspaper_id=newspaper.id,
            message=message,
        )

    def _get_source_from_newspaper(self, newspaper: dict[str, Any]) -> dict[str, Any] | None:
        source_id = newspaper.get("source_id")
        if source_id is None:
            return None
        return self._repository.get_source(int(source_id))

    @staticmethod
    def _build_newspaper_notification_message(source_name: str, newspaper_title: str) -> str:
        return f"{source_name} published a new newspaper: {newspaper_title}"

    @staticmethod
    def _build_article_notification_message(
        source_name: str,
        newspaper_title: str | None,
        article_title: str,
    ) -> str:
        base = f"{source_name} published a new article: {article_title}"
        if newspaper_title:
            return f"{base} in {newspaper_title}"
        return base

    def _inject_public_url(self, record: dict[str, Any]) -> dict[str, Any]:
        enriched = dict(record)
        token = record.get("public_token")
        if token and record.get("is_public"):
            enriched["public_url"] = f"/v1/public/newspapers/{token}"
        else:
            enriched["public_url"] = None
        return enriched

    def _to_newspaper_model(self, record: dict[str, Any]) -> schemas.Newspaper:
        return schemas.Newspaper.model_validate(self._inject_public_url(record))
