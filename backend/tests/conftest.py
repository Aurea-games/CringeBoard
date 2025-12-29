# ruff: noqa: E402
from __future__ import annotations

import os
import sys
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

# Set DATABASE_URL before any app imports to prevent RuntimeError
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")

# Mock psycopg.connect BEFORE importing any app modules
# This prevents ensure_schema() from trying to connect to a real database
_mock_cursor = MagicMock()
_mock_cursor.__enter__ = MagicMock(return_value=_mock_cursor)
_mock_cursor.__exit__ = MagicMock(return_value=False)

_mock_connection = MagicMock()
_mock_connection.__enter__ = MagicMock(return_value=_mock_connection)
_mock_connection.__exit__ = MagicMock(return_value=False)
_mock_connection.cursor = MagicMock(return_value=_mock_cursor)

# Patch psycopg before any imports
import psycopg

_original_connect = psycopg.connect
psycopg.connect = MagicMock(return_value=_mock_connection)

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
        self._next_source_id = 1
        self._next_notification_id = 1
        self._newspapers: dict[int, dict[str, object]] = {}
        self._articles: dict[int, dict[str, object]] = {}
        self._sources: dict[int, dict[str, object]] = {}
        self._followed_sources: dict[int, set[int]] = {}
        self._notifications: dict[int, dict[str, object]] = {}

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def create_newspaper(
        self,
        owner_id: int,
        title: str,
        description: str | None,
        source_id: int | None = None,
    ) -> dict[str, object]:
        newspaper_id = self._next_newspaper_id
        self._next_newspaper_id += 1
        timestamp = self._now()
        record = {
            "id": newspaper_id,
            "title": title,
            "description": description,
            "owner_id": owner_id,
            "is_public": False,
            "public_token": None,
            "created_at": timestamp,
            "updated_at": timestamp,
            "source_id": source_id,
        }
        self._newspapers[newspaper_id] = record
        return record.copy()

    def _clone_article(self, record: dict[str, object]) -> dict[str, object]:
        clone = record.copy()
        clone["newspaper_ids"] = sorted(record.get("newspaper_ids", set()))
        clone["popularity"] = len(record.get("favorite_user_ids", set()))
        clone.pop("favorite_user_ids", None)
        clone.pop("favorite_timestamps", None)
        clone.pop("read_later_user_ids", None)
        clone.pop("read_later_timestamps", None)
        return clone

    def _clone_source(self, record: dict[str, object], follower_id: int | None = None) -> dict[str, object]:
        clone = record.copy()
        if follower_id is not None:
            clone["is_followed"] = record["id"] in self._followed_sources.get(follower_id, set())
        else:
            clone["is_followed"] = False
        return clone

    def _clone_notification(self, record: dict[str, object]) -> dict[str, object]:
        return record.copy()

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
        source_id: int | None = None,
        update_source_id: bool = False,
    ) -> dict[str, object] | None:
        record = self._newspapers.get(newspaper_id)
        if record is None:
            return None
        if title is not None:
            record["title"] = title
        if description is not None:
            record["description"] = description
        if update_source_id:
            record["source_id"] = source_id
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

    def update_newspaper_publication(
        self,
        newspaper_id: int,
        is_public: bool,
        public_token: str | None,
    ) -> dict[str, object] | None:
        record = self._newspapers.get(newspaper_id)
        if record is None:
            return None
        record["is_public"] = is_public
        record["public_token"] = public_token
        record["updated_at"] = self._now()
        return record.copy()

    def get_newspaper_by_token(self, token: str) -> dict[str, object] | None:
        for record in self._newspapers.values():
            if record.get("is_public") and record.get("public_token") == token:
                return record.copy()
        return None

    # ---- Sources ----
    def create_source(
        self,
        name: str,
        feed_url: str | None,
        description: str | None,
        status: str = "active",
    ) -> dict[str, object]:
        source_id = self._next_source_id
        self._next_source_id += 1
        timestamp = self._now()
        record = {
            "id": source_id,
            "name": name,
            "feed_url": feed_url,
            "description": description,
            "status": status or "active",
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        self._sources[source_id] = record
        return self._clone_source(record)

    def list_sources(
        self,
        search: str | None = None,
        status: str | None = None,
        follower_id: int | None = None,
    ) -> list[dict[str, object]]:
        results = list(self._sources.values())
        if status:
            results = [s for s in results if s.get("status") == status]
        if search:
            needle = search.strip().lower()
            if needle:
                filtered = []
                for record in results:
                    name_match = needle in record["name"].lower()
                    desc = record.get("description")
                    desc_match = isinstance(desc, str) and needle in desc.lower()
                    if name_match or desc_match:
                        filtered.append(record)
                results = filtered
        results.sort(key=lambda item: item["created_at"], reverse=True)
        return [self._clone_source(record, follower_id=follower_id) for record in results]

    def get_source(self, source_id: int, follower_id: int | None = None) -> dict[str, object] | None:
        record = self._sources.get(source_id)
        return self._clone_source(record, follower_id=follower_id) if record else None

    def update_source(
        self,
        source_id: int,
        name: str | None,
        feed_url: str | None,
        description: str | None,
        status: str | None,
    ) -> dict[str, object] | None:
        record = self._sources.get(source_id)
        if record is None:
            return None
        if name is not None:
            record["name"] = name
        if feed_url is not None:
            record["feed_url"] = feed_url
        if description is not None:
            record["description"] = description
        if status is not None:
            record["status"] = status
        record["updated_at"] = self._now()
        return self._clone_source(record)

    def follow_source(self, user_id: int, source_id: int) -> dict[str, object] | None:
        if source_id not in self._sources:
            return None
        self._followed_sources.setdefault(user_id, set()).add(source_id)
        return self.get_source(source_id, follower_id=user_id)

    def unfollow_source(self, user_id: int, source_id: int) -> dict[str, object] | None:
        if source_id not in self._sources:
            return None
        self._followed_sources.setdefault(user_id, set()).discard(source_id)
        return self.get_source(source_id, follower_id=user_id)

    def list_followed_sources(self, user_id: int) -> list[dict[str, object]]:
        followed_ids = self._followed_sources.get(user_id, set())
        results = []
        for source_id in followed_ids:
            record = self._sources.get(source_id)
            if record:
                results.append(self._clone_source(record, follower_id=user_id))
        results.sort(key=lambda item: item["created_at"], reverse=True)
        return results

    def search_articles(
        self,
        search: str | None = None,
        owner_id: int | None = None,
        newspaper_id: int | None = None,
        order_by_popularity: bool = False,
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

        if order_by_popularity:
            articles.sort(
                key=lambda item: (len(item.get("favorite_user_ids", set())), item["created_at"]),
                reverse=True,
            )
        else:
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
            "favorite_user_ids": set(),
            "favorite_timestamps": {},
            "read_later_user_ids": set(),
            "read_later_timestamps": {},
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

    def add_article_favorite(self, user_id: int, article_id: int) -> dict[str, object] | None:
        record = self._articles.get(article_id)
        if record is None:
            return None
        favorites = record.setdefault("favorite_user_ids", set())
        favorites.add(user_id)
        record.setdefault("favorite_timestamps", {})[user_id] = self._now()
        return self._clone_article(record)

    def remove_article_favorite(self, user_id: int, article_id: int) -> dict[str, object] | None:
        record = self._articles.get(article_id)
        if record is None:
            return None
        record.setdefault("favorite_user_ids", set()).discard(user_id)
        record.setdefault("favorite_timestamps", {}).pop(user_id, None)
        return self._clone_article(record)

    def list_favorite_articles(self, user_id: int) -> list[dict[str, object]]:
        matches: list[tuple[datetime, dict[str, object]]] = []
        for article in self._articles.values():
            if user_id in article.get("favorite_user_ids", set()):
                timestamp = article.get("favorite_timestamps", {}).get(user_id, article["created_at"])
                matches.append((timestamp, article))
        matches.sort(key=lambda item: item[0], reverse=True)
        return [self._clone_article(article) for _, article in matches]

    def add_read_later(self, user_id: int, article_id: int) -> dict[str, object] | None:
        record = self._articles.get(article_id)
        if record is None:
            return None
        record.setdefault("read_later_user_ids", set()).add(user_id)
        record.setdefault("read_later_timestamps", {})[user_id] = self._now()
        return self._clone_article(record)

    def remove_read_later(self, user_id: int, article_id: int) -> dict[str, object] | None:
        record = self._articles.get(article_id)
        if record is None:
            return None
        record.setdefault("read_later_user_ids", set()).discard(user_id)
        record.setdefault("read_later_timestamps", {}).pop(user_id, None)
        return self._clone_article(record)

    def list_read_later_articles(self, user_id: int) -> list[dict[str, object]]:
        matches: list[tuple[datetime, dict[str, object]]] = []
        for article in self._articles.values():
            if user_id in article.get("read_later_user_ids", set()):
                timestamp = article.get("read_later_timestamps", {}).get(user_id, article["created_at"])
                matches.append((timestamp, article))
        matches.sort(key=lambda item: item[0], reverse=True)
        return [self._clone_article(article) for _, article in matches]

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

    # ---- Notifications ----
    def create_notifications_for_source_followers(
        self,
        source_id: int,
        message: str,
        article_id: int | None = None,
        newspaper_id: int | None = None,
    ) -> int:
        created = 0
        timestamp = self._now()
        for user_id, followed in self._followed_sources.items():
            if source_id not in followed:
                continue
            notification_id = self._next_notification_id
            self._next_notification_id += 1
            record = {
                "id": notification_id,
                "user_id": user_id,
                "source_id": source_id,
                "article_id": article_id,
                "newspaper_id": newspaper_id,
                "message": message,
                "is_read": False,
                "created_at": timestamp,
            }
            self._notifications[notification_id] = record
            created += 1
        return created

    def list_notifications(self, user_id: int, include_read: bool = False) -> list[dict[str, object]]:
        results: list[dict[str, object]] = []
        for record in self._notifications.values():
            if record["user_id"] != user_id:
                continue
            if not include_read and record.get("is_read"):
                continue
            results.append(self._clone_notification(record))
        results.sort(key=lambda item: item["created_at"], reverse=True)
        return results

    def mark_notification_read(self, user_id: int, notification_id: int) -> dict[str, object] | None:
        record = self._notifications.get(notification_id)
        if record is None or record["user_id"] != user_id:
            return None
        record["is_read"] = True
        return self._clone_notification(record)


class InMemoryAuthRepository:
    def __init__(self) -> None:
        self._next_id = 1
        self._ids_by_email: dict[str, int] = {}
        self._emails_by_id: dict[int, str] = {}
        self._passwords: dict[int, str] = {}
        self._preferences: dict[int, dict[str, object]] = {}
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
        self._preferences.pop(user_id, None)
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

    def _get_preferences(self, user_id: int) -> dict[str, object]:
        return self._preferences.setdefault(user_id, {"theme": "light", "hidden_source_ids": set()})

    def get_preferences(self, user_id: int) -> dict[str, object]:
        prefs = self._get_preferences(user_id)
        return {"theme": prefs["theme"], "hidden_source_ids": sorted(prefs["hidden_source_ids"])}

    def update_preferences(
        self,
        user_id: int,
        theme: str | None = None,
        hidden_source_ids: list[int] | None = None,
    ) -> dict[str, object]:
        prefs = self._get_preferences(user_id)
        if theme is not None:
            prefs["theme"] = theme
        if hidden_source_ids is not None:
            prefs["hidden_source_ids"] = set(hidden_source_ids)
        return self.get_preferences(user_id)

    def add_hidden_source(self, user_id: int, source_id: int) -> dict[str, object]:
        prefs = self._get_preferences(user_id)
        prefs["hidden_source_ids"].add(source_id)
        return self.get_preferences(user_id)

    def remove_hidden_source(self, user_id: int, source_id: int) -> dict[str, object]:
        prefs = self._get_preferences(user_id)
        prefs["hidden_source_ids"].discard(source_id)
        return self.get_preferences(user_id)

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

    def register_user(self, email: str, password: str) -> TokenResponse:
        self.ensure_email_allowed(email)
        if self._repository.email_exists(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email is already registered.",
            )
        password_hash = self._hasher.hash(password)
        user_id = self._repository.create_user(email, password_hash)
        return self.issue_tokens(user_id)

    def authenticate(self, email: str, password: str) -> TokenResponse:
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

    def refresh_tokens(self, refresh_token: str) -> TokenResponse:
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

    def issue_tokens(self, user_id: int) -> TokenResponse:
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
        def __enter__(self) -> DummyCursor:
            return self

        def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
            return False

        def execute(self, *args, **kwargs) -> None:
            return None

    class DummyConnection:
        def __enter__(self) -> DummyConnection:
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

    from app.api.routes.aggregator import dependencies as aggregator_dependencies
    from app.api.routes.aggregator.services import AggregatorService
    from app.api.routes.auth import delete, dependencies, login, profile, refresh, register
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
    monkeypatch.setattr(profile, "auth_repository", repository)

    aggregator_repository = InMemoryAggregatorRepository()
    aggregator_service = AggregatorService(aggregator_repository, repository)
    monkeypatch.setattr(aggregator_dependencies, "aggregator_repository", aggregator_repository)
    monkeypatch.setattr(aggregator_dependencies, "aggregator_service", aggregator_service)

    app = create_application()
    with TestClient(app) as client:
        yield client
