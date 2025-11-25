from __future__ import annotations

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
        return [schemas.Newspaper.model_validate(row) for row in rows]

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
        record = self._repository.create_newspaper(owner_id, title, description)
        return schemas.Newspaper.model_validate(record)

    def get_newspaper(self, newspaper_id: int) -> schemas.NewspaperDetail:
        record = self._repository.get_newspaper(newspaper_id)
        if record is None:
            raise self._NEWSPAPER_NOT_FOUND
        articles = self._repository.search_articles(newspaper_id=newspaper_id)
        return schemas.NewspaperDetail.from_parts(record, articles)

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
        record = self._repository.update_newspaper(newspaper_id, title, description)
        if record is None:
            raise self._NEWSPAPER_NOT_FOUND
        return schemas.Newspaper.model_validate(record)

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
    ) -> list[schemas.Article]:
        owner_id: int | None = None
        if owner_email:
            normalized = normalize_email(owner_email)
            owner_id = self._auth_repository.get_user_id(normalized)
            if owner_id is None:
                return []

        rows = self._repository.search_articles(search=search, owner_id=owner_id, newspaper_id=newspaper_id)
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
        return schemas.Article.model_validate(record)

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
        return schemas.Article.model_validate(record)

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
