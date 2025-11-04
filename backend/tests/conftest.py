from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import TYPE_CHECKING

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

if TYPE_CHECKING:
    from app.api.routes.auth.schemas import TokenResponse


class SimplePasswordHasher:
    def hash(self, password: str) -> str:
        return f"hashed::{password}"

    def verify(self, password: str, password_hash: str) -> bool:
        return password_hash == f"hashed::{password}"


class DeterministicTokenGenerator:
    def __init__(self) -> None:
        self._counter = 0

    def __call__(self, _: int) -> str:
        self._counter += 1
        return f"token-{self._counter}"


class InMemoryAggregatorRepository:
    def __init__(self) -> None:
        self._next_newspaper_id = 1
        self._next_article_id = 1
        self._newspapers: dict[int, dict[str, object]] = {}
        self._articles: dict[int, dict[str, object]] = {}

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def create_newspaper(self, owner_id: int, title: str, description: str | None) -> dict[str, object]:
        newspaper_id = self._next_newspaper_id
        self._next_newspaper_id += 1
        timestamp = self._now()
        record = {
            "id": newspaper_id,
            "title": title,
            "description": description,
            "owner_id": owner_id,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        self._newspapers[newspaper_id] = record
        return record.copy()

    def _clone_article(self, record: dict[str, object]) -> dict[str, object]:
        clone = record.copy()
        clone["newspaper_ids"] = sorted(record.get("newspaper_ids", set()))
        return clone

    def list_newspapers(self) -> list[dict[str, object]]:
        return self.search_newspapers()

    def search_newspapers(
        self,
        search: str | None = None,
        owner_id: int | None = None,
    ) -> list[dict[str, object]]:
        results = list(self._newspapers.values())
        if owner_id is not None:
            results = [record for record in results if record["owner_id"] == owner_id]
        if search:
            needle = search.strip().lower()
            if needle:
                filtered: list[dict[str, object]] = []
                for record in results:
                    title_match = needle in record["title"].lower()
                    description = record.get("description")
                    description_match = isinstance(description, str) and needle in description.lower()
                    if title_match or description_match:
                        filtered.append(record)
                results = filtered

        results.sort(key=lambda item: item["created_at"], reverse=True)
        return [record.copy() for record in results]

    def find_newspaper_by_title(self, owner_id: int, title: str) -> dict[str, object] | None:
        for record in self._newspapers.values():
            if record["owner_id"] == owner_id and record["title"] == title:
                return record.copy()
        return None

    def get_newspaper(self, newspaper_id: int) -> dict[str, object] | None:
        record = self._newspapers.get(newspaper_id)
        return record.copy() if record else None

    def update_newspaper(
        self,
        newspaper_id: int,
        title: str | None,
        description: str | None,
    ) -> dict[str, object] | None:
        record = self._newspapers.get(newspaper_id)
        if record is None:
            return None
        if title is not None:
            record["title"] = title
        if description is not None:
            record["description"] = description
        record["updated_at"] = self._now()
        return record.copy()

    def delete_newspaper(self, newspaper_id: int) -> bool:
        removed = self._newspapers.pop(newspaper_id, None)
        if removed is None:
            return False
        for article in self._articles.values():
            ids = article.setdefault("newspaper_ids", set())
            if newspaper_id in ids:
                ids.discard(newspaper_id)
        return True

    def list_articles_for_newspaper(self, newspaper_id: int) -> list[dict[str, object]]:
        return self.search_articles(newspaper_id=newspaper_id)

    def search_articles(
        self,
        search: str | None = None,
        owner_id: int | None = None,
        newspaper_id: int | None = None,
    ) -> list[dict[str, object]]:
        articles = list(self._articles.values())
        if owner_id is not None:
            articles = [article for article in articles if article["owner_id"] == owner_id]
        if newspaper_id is not None:
            articles = [article for article in articles if newspaper_id in article.get("newspaper_ids", set())]
        if search:
            needle = search.strip().lower()
            if needle:
                filtered_articles: list[dict[str, object]] = []
                for article in articles:
                    title_match = needle in article["title"].lower()
                    content = article.get("content")
                    content_match = isinstance(content, str) and needle in content.lower()
                    if title_match or content_match:
                        filtered_articles.append(article)
                articles = filtered_articles

        articles.sort(key=lambda item: item["created_at"], reverse=True)
        return [self._clone_article(article) for article in articles]

    def create_article(
        self,
        owner_id: int,
        newspaper_id: int,
        title: str,
        content: str | None,
        url: str | None,
    ) -> dict[str, object]:
        article_id = self._next_article_id
        self._next_article_id += 1
        timestamp = self._now()
        record = {
            "id": article_id,
            "title": title,
            "content": content,
            "url": url,
            "owner_id": owner_id,
            "created_at": timestamp,
            "updated_at": timestamp,
            "newspaper_ids": {newspaper_id},
        }
        self._articles[article_id] = record
        return self._clone_article(record)

    def get_article(self, article_id: int) -> dict[str, object] | None:
        record = self._articles.get(article_id)
        return self._clone_article(record) if record else None

    def find_article_by_url(self, url: str) -> dict[str, object] | None:
        for record in self._articles.values():
            if record.get("url") == url:
                return self._clone_article(record)
        return None

    def update_article(
        self,
        article_id: int,
        title: str | None,
        content: str | None,
        url: str | None,
    ) -> dict[str, object] | None:
        record = self._articles.get(article_id)
        if record is None:
            return None
        if title is not None:
            record["title"] = title
        if content is not None:
            record["content"] = content
        if url is not None:
            record["url"] = url
        record["updated_at"] = self._now()
        return self._clone_article(record)

    def assign_article_to_newspaper(self, article_id: int, newspaper_id: int) -> dict[str, object] | None:
        record = self._articles.get(article_id)
        if record is None:
            return None
        record.setdefault("newspaper_ids", set()).add(newspaper_id)
        record["updated_at"] = self._now()
        return self._clone_article(record)

    def delete_article(self, article_id: int) -> bool:
        return self._articles.pop(article_id, None) is not None


class InMemoryAuthRepository:
    def __init__(self) -> None:
        self._next_id = 1
        self._ids_by_email: dict[str, int] = {}
        self._emails_by_id: dict[int, str] = {}
        self._passwords: dict[int, str] = {}
        self._user_tokens: dict[int, dict[str, str]] = {}
        self._token_index: dict[str, tuple[str, int]] = {}

    def email_exists(self, email: str) -> bool:
        return email in self._ids_by_email

    def create_user(self, email: str, password_hash: str) -> int:
        user_id = self._next_id
        self._next_id += 1
        self._ids_by_email[email] = user_id
        self._emails_by_id[user_id] = email
        self._passwords[user_id] = password_hash
        return user_id

    def get_user_credentials(self, email: str) -> tuple[int, str] | None:
        user_id = self._ids_by_email.get(email)
        if user_id is None:
            return None
        password_hash = self._passwords.get(user_id)
        if password_hash is None:
            return None
        return user_id, password_hash

    def get_user_id(self, email: str) -> int | None:
        return self._ids_by_email.get(email)

    def delete_user(self, user_id: int) -> bool:
        email = self._emails_by_id.pop(user_id, None)
        if email is None:
            return False
        self._ids_by_email.pop(email, None)
        self._passwords.pop(user_id, None)
        self.delete_tokens_for_user(user_id)
        return True

    def store_tokens(self, user_id: int, access_token: str, refresh_token: str) -> None:
        self.delete_tokens_for_user(user_id)
        self._token_index[access_token] = ("access", user_id)
        self._token_index[refresh_token] = ("refresh", user_id)
        self._user_tokens[user_id] = {
            "access": access_token,
            "refresh": refresh_token,
        }

    def get_email_by_access_token(self, token: str) -> str | None:
        entry = self._token_index.get(token)
        if entry is None or entry[0] != "access":
            return None
        _, user_id = entry
        return self._emails_by_id.get(user_id)

    def get_user_id_by_refresh_token(self, token: str) -> int | None:
        entry = self._token_index.get(token)
        if entry is None or entry[0] != "refresh":
            return None
        return entry[1]

    def delete_tokens_for_user(self, user_id: int) -> None:
        tokens = self._user_tokens.pop(user_id, None)
        if not tokens:
            return
        for token in tokens.values():
            self._token_index.pop(token, None)


class FakeAuthService:
    _BLOCKED_SUFFIXES = ("@example.com",)

    def __init__(
        self,
        repository: InMemoryAuthRepository,
        hasher: SimplePasswordHasher,
        token_generator: DeterministicTokenGenerator,
    ) -> None:
        self._repository = repository
        self._hasher = hasher
        self._token_generator = token_generator

    def register_user(self, email: str, password: str) -> "TokenResponse":
        self.ensure_email_allowed(email)
        if self._repository.email_exists(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email is already registered.",
            )
        password_hash = self._hasher.hash(password)
        user_id = self._repository.create_user(email, password_hash)
        return self.issue_tokens(user_id)

    def authenticate(self, email: str, password: str) -> "TokenResponse":
        credentials = self._repository.get_user_credentials(email)
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials.",
            )

        user_id, stored_hash = credentials
        if not self._hasher.verify(password, stored_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials.",
            )
        return self.issue_tokens(user_id)

    def remove_user(self, email: str) -> None:
        user_id = self._repository.get_user_id(email)
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        self._repository.delete_tokens_for_user(user_id)
        if not self._repository.delete_user(user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

    def refresh_tokens(self, refresh_token: str) -> "TokenResponse":
        normalized_token = refresh_token.strip()
        if not normalized_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token must not be empty.",
            )
        user_id = self._repository.get_user_id_by_refresh_token(normalized_token)
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
            )
        return self.issue_tokens(user_id)

    def ensure_email_allowed(self, email: str) -> None:
        if email.endswith(self._BLOCKED_SUFFIXES):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration with example.com emails is not allowed.",
            )

    def issue_tokens(self, user_id: int) -> "TokenResponse":
        from app.api.routes.auth.schemas import TokenResponse

        access_token = self._token_generator(32)
        refresh_token = self._token_generator(48)
        self._repository.store_tokens(user_id, access_token, refresh_token)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )


@pytest.fixture
def auth_test_client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    import psycopg

    class DummyCursor:
        def __enter__(self) -> "DummyCursor":
            return self

        def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
            return False

        def execute(self, *args, **kwargs) -> None:
            return None

    class DummyConnection:
        def __enter__(self) -> "DummyConnection":
            return self

        def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
            return False

        def cursor(self) -> DummyCursor:
            return DummyCursor()

        def commit(self) -> None:
            return None

        def rollback(self) -> None:
            return None

        def close(self) -> None:
            return None

    def fake_connect(*args, **kwargs) -> DummyConnection:
        return DummyConnection()

    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/test-db")
    monkeypatch.setattr(psycopg, "connect", fake_connect)

    from app.api.routes.auth import delete, dependencies, login, refresh, register
    from app.api.routes.aggregator import dependencies as aggregator_dependencies
    from app.api.routes.aggregator.services import AggregatorService
    from app.main import create_application

    repository = InMemoryAuthRepository()
    token_generator = DeterministicTokenGenerator()
    password_hasher = SimplePasswordHasher()
    auth_service = FakeAuthService(repository, password_hasher, token_generator)

    monkeypatch.setattr(dependencies, "auth_repository", repository)
    monkeypatch.setattr(dependencies, "auth_service", auth_service)
    monkeypatch.setattr(login, "auth_service", auth_service)
    monkeypatch.setattr(register, "auth_service", auth_service)
    monkeypatch.setattr(refresh, "auth_service", auth_service)
    monkeypatch.setattr(delete, "auth_service", auth_service)

    aggregator_repository = InMemoryAggregatorRepository()
    aggregator_service = AggregatorService(aggregator_repository, repository)
    monkeypatch.setattr(aggregator_dependencies, "aggregator_repository", aggregator_repository)
    monkeypatch.setattr(aggregator_dependencies, "aggregator_service", aggregator_service)

    app = create_application()
    with TestClient(app) as client:
        yield client
