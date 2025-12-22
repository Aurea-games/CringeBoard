"""Unit tests for AggregatorRepository with mocked database connections."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from app.api.routes.aggregator.repository import AggregatorRepository


class MockCursor:
    """Mock database cursor for testing."""

    def __init__(self, rows: list[tuple] | None = None, rowcount: int = 0) -> None:
        self._rows = rows or []
        self._index = 0
        self.rowcount = rowcount
        self.executed_queries: list[tuple[str, tuple]] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def execute(self, query: str, params: tuple = ()) -> None:
        self.executed_queries.append((query, params))

    def fetchone(self) -> tuple | None:
        if self._index < len(self._rows):
            row = self._rows[self._index]
            self._index += 1
            return row
        return None

    def fetchall(self) -> list[tuple]:
        result = self._rows[self._index :]
        self._index = len(self._rows)
        return result


class MockConnection:
    """Mock database connection for testing."""

    def __init__(self, cursor: MockCursor) -> None:
        self._cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def cursor(self) -> MockCursor:
        return self._cursor


def create_mock_connection_factory(cursor: MockCursor):
    """Create a connection factory that returns a mock connection."""

    def factory():
        return MockConnection(cursor)

    return factory


class TestRowConversions:
    """Test static row-to-dict conversion methods."""

    def test_row_to_newspaper_returns_none_for_none(self):
        result = AggregatorRepository.row_to_newspaper(None)
        assert result is None

    def test_row_to_newspaper_converts_row(self):
        now = datetime.now(timezone.utc)
        row = (1, "Title", "Description", 10, True, "token123", now, now, 5)
        result = AggregatorRepository.row_to_newspaper(row)
        assert result == {
            "id": 1,
            "title": "Title",
            "description": "Description",
            "owner_id": 10,
            "is_public": True,
            "public_token": "token123",
            "created_at": now,
            "updated_at": now,
            "source_id": 5,
        }

    def test_normalize_newspaper_ids_returns_empty_for_none(self):
        result = AggregatorRepository.normalize_newspaper_ids(None)
        assert result == []

    def test_normalize_newspaper_ids_converts_ids(self):
        result = AggregatorRepository.normalize_newspaper_ids([1, 2, 3])
        assert result == [1, 2, 3]

    def test_normalize_newspaper_ids_converts_string_ids(self):
        result = AggregatorRepository.normalize_newspaper_ids(["1", "2", "3"])
        assert result == [1, 2, 3]

    def test_row_to_article_returns_none_for_none(self):
        result = AggregatorRepository.row_to_article(None)
        assert result is None

    def test_row_to_article_converts_row(self):
        now = datetime.now(timezone.utc)
        row = (1, "Article Title", "Content", "http://example.com", 10, 5, now, now, [1, 2])
        result = AggregatorRepository.row_to_article(row)
        assert result == {
            "id": 1,
            "title": "Article Title",
            "content": "Content",
            "url": "http://example.com",
            "owner_id": 10,
            "popularity": 5,
            "created_at": now,
            "updated_at": now,
            "newspaper_ids": [1, 2],
        }

    def test_row_to_source_returns_none_for_none(self):
        result = AggregatorRepository.row_to_source(None)
        assert result is None

    def test_row_to_source_converts_row_without_is_followed(self):
        now = datetime.now(timezone.utc)
        row = (1, "Source Name", "http://feed.url", "Description", "active", now, now)
        result = AggregatorRepository.row_to_source(row)
        assert result == {
            "id": 1,
            "name": "Source Name",
            "feed_url": "http://feed.url",
            "description": "Description",
            "status": "active",
            "created_at": now,
            "updated_at": now,
            "is_followed": False,
        }

    def test_row_to_source_converts_row_with_is_followed(self):
        now = datetime.now(timezone.utc)
        row = (1, "Source Name", "http://feed.url", "Description", "active", now, now, True)
        result = AggregatorRepository.row_to_source(row)
        assert result["is_followed"] is True

    def test_row_to_notification_returns_none_for_none(self):
        result = AggregatorRepository.row_to_notification(None)
        assert result is None

    def test_row_to_notification_converts_row(self):
        now = datetime.now(timezone.utc)
        row = (1, 10, 5, 100, 50, "New article!", False, now)
        result = AggregatorRepository.row_to_notification(row)
        assert result == {
            "id": 1,
            "user_id": 10,
            "source_id": 5,
            "article_id": 100,
            "newspaper_id": 50,
            "message": "New article!",
            "is_read": False,
            "created_at": now,
        }

    def test_row_to_custom_feed_returns_none_for_none(self):
        result = AggregatorRepository.row_to_custom_feed(None)
        assert result is None

    def test_row_to_custom_feed_converts_row_with_dict(self):
        now = datetime.now(timezone.utc)
        filter_rules = {"include_keywords": ["python"]}
        row = (1, 10, "My Feed", "Description", filter_rules, now, now)
        result = AggregatorRepository.row_to_custom_feed(row)
        assert result == {
            "id": 1,
            "owner_id": 10,
            "name": "My Feed",
            "description": "Description",
            "filter_rules": filter_rules,
            "created_at": now,
            "updated_at": now,
        }

    def test_row_to_custom_feed_converts_row_with_json_string(self):
        now = datetime.now(timezone.utc)
        filter_rules_json = '{"include_keywords": ["python"]}'
        row = (1, 10, "My Feed", "Description", filter_rules_json, now, now)
        result = AggregatorRepository.row_to_custom_feed(row)
        assert result["filter_rules"] == {"include_keywords": ["python"]}


class TestNewspaperOperations:
    """Test newspaper CRUD operations."""

    def test_create_newspaper_success(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Test Paper", "A description", 10, False, None, now, now, None)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.create_newspaper(owner_id=10, title="Test Paper", description="A description")

        assert result["id"] == 1
        assert result["title"] == "Test Paper"
        assert result["owner_id"] == 10

    def test_create_newspaper_with_source_id(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Test Paper", "Desc", 10, False, None, now, now, 5)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.create_newspaper(owner_id=10, title="Test Paper", description="Desc", source_id=5)

        assert result["source_id"] == 5

    def test_create_newspaper_raises_on_failure(self):
        cursor = MockCursor(rows=[])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        with pytest.raises(RuntimeError, match="Failed to create newspaper"):
            repo.create_newspaper(owner_id=10, title="Test", description=None)

    def test_list_newspapers_calls_search(self):
        cursor = MockCursor(rows=[])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.list_newspapers()
        assert result == []

    def test_search_newspapers_with_owner_id(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Paper", "Desc", 10, False, None, now, now, None)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.search_newspapers(owner_id=10)

        assert len(result) == 1
        assert result[0]["owner_id"] == 10

    def test_search_newspapers_with_search_term(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Python News", "Desc", 10, False, None, now, now, None)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.search_newspapers(search="python")

        assert len(result) == 1

    def test_search_newspapers_with_empty_search(self):
        cursor = MockCursor(rows=[])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.search_newspapers(search="   ")
        assert result == []

    def test_find_newspaper_by_title(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "My Paper", "Desc", 10, False, None, now, now, None)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.find_newspaper_by_title(owner_id=10, title="My Paper")

        assert result is not None
        assert result["title"] == "My Paper"

    def test_find_newspaper_by_title_not_found(self):
        cursor = MockCursor(rows=[])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.find_newspaper_by_title(owner_id=10, title="Nonexistent")

        assert result is None

    def test_get_newspaper(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Paper", "Desc", 10, True, "token", now, now, 5)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.get_newspaper(newspaper_id=1)

        assert result is not None
        assert result["id"] == 1

    def test_get_newspaper_not_found(self):
        cursor = MockCursor(rows=[])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.get_newspaper(newspaper_id=999)

        assert result is None

    def test_update_newspaper_with_title_only(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "New Title", "Desc", 10, False, None, now, now, None)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.update_newspaper(newspaper_id=1, title="New Title", description=None, source_id=None)

        assert result is not None
        assert result["title"] == "New Title"

    def test_update_newspaper_with_description(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Title", "New Desc", 10, False, None, now, now, None)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.update_newspaper(newspaper_id=1, title=None, description="New Desc", source_id=None)

        assert result is not None

    def test_update_newspaper_with_source_id(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Title", "Desc", 10, False, None, now, now, 5)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.update_newspaper(newspaper_id=1, title=None, description=None, source_id=5, update_source_id=True)

        assert result is not None
        assert result["source_id"] == 5

    def test_update_newspaper_not_found(self):
        cursor = MockCursor(rows=[])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.update_newspaper(newspaper_id=999, title="Title", description=None, source_id=None)

        assert result is None

    def test_delete_newspaper_success(self):
        cursor = MockCursor(rowcount=1)
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.delete_newspaper(newspaper_id=1)

        assert result is True

    def test_delete_newspaper_not_found(self):
        cursor = MockCursor(rowcount=0)
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.delete_newspaper(newspaper_id=999)

        assert result is False

    def test_update_newspaper_publication(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Paper", "Desc", 10, True, "new-token", now, now, None)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.update_newspaper_publication(newspaper_id=1, is_public=True, public_token="new-token")

        assert result is not None
        assert result["is_public"] is True
        assert result["public_token"] == "new-token"

    def test_update_newspaper_publication_not_found(self):
        cursor = MockCursor(rows=[])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.update_newspaper_publication(newspaper_id=999, is_public=True, public_token="token")

        assert result is None

    def test_get_newspaper_by_token(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Public Paper", "Desc", 10, True, "token123", now, now, None)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.get_newspaper_by_token(token="token123")

        assert result is not None
        assert result["public_token"] == "token123"

    def test_get_newspaper_by_token_not_found(self):
        cursor = MockCursor(rows=[])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.get_newspaper_by_token(token="invalid")

        assert result is None


class TestArticleOperations:
    """Test article CRUD operations."""

    def test_list_articles_for_newspaper(self):
        cursor = MockCursor(rows=[])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.list_articles_for_newspaper(newspaper_id=1)

        assert result == []

    def test_search_articles_with_newspaper_id(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Article", "Content", "http://url.com", 10, 5, now, now, [1])])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.search_articles(newspaper_id=1)

        assert len(result) == 1

    def test_search_articles_with_owner_id(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Article", "Content", "http://url.com", 10, 0, now, now, [])])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.search_articles(owner_id=10)

        assert len(result) == 1

    def test_search_articles_with_search_term(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Python Tutorial", "Learn Python", "http://url.com", 10, 0, now, now, [])])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.search_articles(search="python")

        assert len(result) == 1

    def test_search_articles_order_by_popularity(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(
            rows=[
                (1, "Popular", "Content", "http://url.com", 10, 100, now, now, []),
                (2, "Less Popular", "Content", "http://url.com", 10, 10, now, now, []),
            ]
        )
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.search_articles(order_by_popularity=True)

        assert len(result) == 2

    def test_create_article_success(self):
        now = datetime.now(timezone.utc)
        # First call returns article id, second call (fetch_article) returns full article
        cursor = MockCursor(rows=[(1,), (1, "Article", "Content", "http://url.com", 10, 0, now, now, [1])])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.create_article(
            owner_id=10, newspaper_id=1, title="Article", content="Content", url="http://url.com"
        )

        assert result["id"] == 1
        assert result["title"] == "Article"

    def test_create_article_raises_on_insert_failure(self):
        cursor = MockCursor(rows=[])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        with pytest.raises(RuntimeError, match="Failed to create article"):
            repo.create_article(owner_id=10, newspaper_id=1, title="Article", content=None, url=None)

    def test_get_article(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Article", "Content", "http://url.com", 10, 5, now, now, [1, 2])])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.get_article(article_id=1)

        assert result is not None
        assert result["id"] == 1

    def test_get_article_not_found(self):
        cursor = MockCursor(rows=[])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.get_article(article_id=999)

        assert result is None

    def test_get_related_articles(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(2, "Related", "Content", "http://url.com", 10, 3, now, now, [1])])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.get_related_articles(article_id=1, limit=10)

        assert len(result) == 1
        assert result[0]["id"] == 2

    def test_add_article_favorite(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Article", "Content", "http://url.com", 10, 1, now, now, [1])])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.add_article_favorite(user_id=5, article_id=1)

        assert result is not None

    def test_remove_article_favorite(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Article", "Content", "http://url.com", 10, 0, now, now, [1])])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.remove_article_favorite(user_id=5, article_id=1)

        assert result is not None

    def test_list_favorite_articles(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Article", "Content", "http://url.com", 10, 5, now, now, [1])])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.list_favorite_articles(user_id=5)

        assert len(result) == 1

    def test_add_read_later(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Article", "Content", "http://url.com", 10, 0, now, now, [1])])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.add_read_later(user_id=5, article_id=1)

        assert result is not None

    def test_remove_read_later(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Article", "Content", "http://url.com", 10, 0, now, now, [1])])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.remove_read_later(user_id=5, article_id=1)

        assert result is not None

    def test_list_read_later_articles(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Article", "Content", "http://url.com", 10, 0, now, now, [1])])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.list_read_later_articles(user_id=5)

        assert len(result) == 1

    def test_find_article_by_url(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Article", "Content", "http://example.com/article", 10, 0, now, now, [1])])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.find_article_by_url(url="http://example.com/article")

        assert result is not None
        assert result["url"] == "http://example.com/article"

    def test_find_article_by_url_not_found(self):
        cursor = MockCursor(rows=[])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.find_article_by_url(url="http://nonexistent.com")

        assert result is None

    def test_update_article_with_title(self):
        now = datetime.now(timezone.utc)
        # First fetchone for the UPDATE RETURNING, second for fetch_article
        cursor = MockCursor(rows=[(1,), (1, "New Title", "Content", "http://url.com", 10, 0, now, now, [1])])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.update_article(article_id=1, title="New Title", content=None, url=None)

        assert result is not None

    def test_update_article_with_content(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1,), (1, "Title", "New Content", "http://url.com", 10, 0, now, now, [1])])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.update_article(article_id=1, title=None, content="New Content", url=None)

        assert result is not None

    def test_update_article_with_url(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1,), (1, "Title", "Content", "http://newurl.com", 10, 0, now, now, [1])])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.update_article(article_id=1, title=None, content=None, url="http://newurl.com")

        assert result is not None

    def test_update_article_not_found(self):
        cursor = MockCursor(rows=[])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.update_article(article_id=999, title="Title", content=None, url=None)

        assert result is None

    def test_assign_article_to_newspaper(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Article", "Content", "http://url.com", 10, 0, now, now, [1, 2])])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.assign_article_to_newspaper(article_id=1, newspaper_id=2)

        assert result is not None

    def test_detach_article_from_newspaper(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Article", "Content", "http://url.com", 10, 0, now, now, [1])])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.detach_article_from_newspaper(article_id=1, newspaper_id=2)

        assert result is not None

    def test_delete_article_success(self):
        cursor = MockCursor(rowcount=1)
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.delete_article(article_id=1)

        assert result is True

    def test_delete_article_not_found(self):
        cursor = MockCursor(rowcount=0)
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.delete_article(article_id=999)

        assert result is False


class TestSourceOperations:
    """Test source CRUD operations."""

    def test_create_source_success(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Source", "http://feed.url", "Description", "active", now, now)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.create_source(name="Source", feed_url="http://feed.url", description="Description")

        assert result["id"] == 1
        assert result["name"] == "Source"

    def test_create_source_with_status(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Source", "http://feed.url", None, "inactive", now, now)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.create_source(name="Source", feed_url="http://feed.url", description=None, status="inactive")

        assert result["status"] == "inactive"

    def test_create_source_raises_on_failure(self):
        cursor = MockCursor(rows=[])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        with pytest.raises(RuntimeError, match="Failed to create source"):
            repo.create_source(name="Source", feed_url=None, description=None)

    def test_list_sources(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Source", "http://feed.url", "Desc", "active", now, now)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.list_sources()

        assert len(result) == 1

    def test_list_sources_with_status_filter(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Source", "http://feed.url", "Desc", "active", now, now)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.list_sources(status="active")

        assert len(result) == 1

    def test_list_sources_with_search(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Python Feed", "http://feed.url", "Desc", "active", now, now)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.list_sources(search="python")

        assert len(result) == 1

    def test_list_sources_with_follower_id(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Source", "http://feed.url", "Desc", "active", now, now, True)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.list_sources(follower_id=5)

        assert len(result) == 1
        assert result[0]["is_followed"] is True

    def test_get_source(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Source", "http://feed.url", "Desc", "active", now, now)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.get_source(source_id=1)

        assert result is not None
        assert result["id"] == 1

    def test_get_source_with_follower_id(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Source", "http://feed.url", "Desc", "active", now, now, True)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.get_source(source_id=1, follower_id=5)

        assert result is not None
        assert result["is_followed"] is True

    def test_get_source_not_found(self):
        cursor = MockCursor(rows=[])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.get_source(source_id=999)

        assert result is None

    def test_update_source_with_name(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "New Name", "http://feed.url", "Desc", "active", now, now)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.update_source(source_id=1, name="New Name", feed_url=None, description=None, status=None)

        assert result is not None
        assert result["name"] == "New Name"

    def test_update_source_with_all_fields(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "New Name", "http://new.url", "New Desc", "inactive", now, now)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.update_source(
            source_id=1, name="New Name", feed_url="http://new.url", description="New Desc", status="inactive"
        )

        assert result is not None

    def test_update_source_not_found(self):
        cursor = MockCursor(rows=[])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.update_source(source_id=999, name="Name", feed_url=None, description=None, status=None)

        assert result is None

    def test_follow_source(self):
        now = datetime.now(timezone.utc)
        # First for INSERT, second for get_source
        cursor = MockCursor(rows=[(1, "Source", "http://feed.url", "Desc", "active", now, now, True)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.follow_source(user_id=5, source_id=1)

        assert result is not None

    def test_unfollow_source(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Source", "http://feed.url", "Desc", "active", now, now, False)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.unfollow_source(user_id=5, source_id=1)

        assert result is not None

    def test_list_followed_sources(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Source", "http://feed.url", "Desc", "active", now, now, True)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.list_followed_sources(user_id=5)

        assert len(result) == 1


class TestNotificationOperations:
    """Test notification operations."""

    def test_create_notifications_for_source_followers(self):
        cursor = MockCursor(rowcount=3)
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.create_notifications_for_source_followers(
            source_id=1, message="New article!", article_id=10, newspaper_id=5
        )

        assert result == 3

    def test_list_notifications(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, 5, 1, 10, 5, "Message", False, now)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.list_notifications(user_id=5)

        assert len(result) == 1

    def test_list_notifications_include_read(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, 5, 1, 10, 5, "Message", True, now)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.list_notifications(user_id=5, include_read=True)

        assert len(result) == 1

    def test_mark_notification_read(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, 5, 1, 10, 5, "Message", True, now)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.mark_notification_read(user_id=5, notification_id=1)

        assert result is not None
        assert result["is_read"] is True

    def test_mark_notification_read_not_found(self):
        cursor = MockCursor(rows=[])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.mark_notification_read(user_id=5, notification_id=999)

        assert result is None


class TestCustomFeedOperations:
    """Test custom feed CRUD operations."""

    def test_create_custom_feed_success(self):
        now = datetime.now(timezone.utc)
        filter_rules = {"include_keywords": ["python"]}
        cursor = MockCursor(rows=[(1, 10, "My Feed", "Description", filter_rules, now, now)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.create_custom_feed(
            owner_id=10, name="My Feed", description="Description", filter_rules=filter_rules
        )

        assert result["id"] == 1
        assert result["name"] == "My Feed"

    def test_create_custom_feed_raises_on_failure(self):
        cursor = MockCursor(rows=[])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        with pytest.raises(RuntimeError, match="Failed to create custom feed"):
            repo.create_custom_feed(owner_id=10, name="Feed", description=None, filter_rules={})

    def test_list_custom_feeds(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, 10, "Feed 1", "Desc", {}, now, now), (2, 10, "Feed 2", None, {}, now, now)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.list_custom_feeds(owner_id=10)

        assert len(result) == 2

    def test_get_custom_feed(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, 10, "My Feed", "Desc", {"include_keywords": ["python"]}, now, now)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.get_custom_feed(custom_feed_id=1)

        assert result is not None
        assert result["id"] == 1

    def test_get_custom_feed_not_found(self):
        cursor = MockCursor(rows=[])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.get_custom_feed(custom_feed_id=999)

        assert result is None

    def test_update_custom_feed_with_name(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, 10, "New Name", "Desc", {}, now, now)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.update_custom_feed(custom_feed_id=1, name="New Name", description=None, filter_rules=None)

        assert result is not None
        assert result["name"] == "New Name"

    def test_update_custom_feed_with_description(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, 10, "Feed", "New Desc", {}, now, now)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.update_custom_feed(custom_feed_id=1, name=None, description="New Desc", filter_rules=None)

        assert result is not None

    def test_update_custom_feed_with_filter_rules(self):
        now = datetime.now(timezone.utc)
        new_rules = {"exclude_keywords": ["spam"]}
        cursor = MockCursor(rows=[(1, 10, "Feed", "Desc", new_rules, now, now)])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.update_custom_feed(custom_feed_id=1, name=None, description=None, filter_rules=new_rules)

        assert result is not None

    def test_update_custom_feed_not_found(self):
        cursor = MockCursor(rows=[])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.update_custom_feed(custom_feed_id=999, name="Name", description=None, filter_rules=None)

        assert result is None

    def test_delete_custom_feed_success(self):
        cursor = MockCursor(rowcount=1)
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.delete_custom_feed(custom_feed_id=1)

        assert result is True

    def test_delete_custom_feed_not_found(self):
        cursor = MockCursor(rowcount=0)
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.delete_custom_feed(custom_feed_id=999)

        assert result is False

    def test_get_articles_for_custom_feed_with_include_sources(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Article", "Content", "http://url.com", 10, 5, now, now, [1])])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.get_articles_for_custom_feed(filter_rules={"include_sources": [1, 2]}, limit=50, offset=0)

        assert len(result) == 1

    def test_get_articles_for_custom_feed_with_exclude_sources(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Article", "Content", "http://url.com", 10, 5, now, now, [1])])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.get_articles_for_custom_feed(filter_rules={"exclude_sources": [3]}, limit=50, offset=0)

        assert len(result) == 1

    def test_get_articles_for_custom_feed_with_include_newspapers(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Article", "Content", "http://url.com", 10, 5, now, now, [1])])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.get_articles_for_custom_feed(filter_rules={"include_newspapers": [1]}, limit=50, offset=0)

        assert len(result) == 1

    def test_get_articles_for_custom_feed_with_include_keywords(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Python Article", "Content", "http://url.com", 10, 5, now, now, [1])])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.get_articles_for_custom_feed(filter_rules={"include_keywords": ["python"]}, limit=50, offset=0)

        assert len(result) == 1

    def test_get_articles_for_custom_feed_with_exclude_keywords(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Article", "Content", "http://url.com", 10, 5, now, now, [1])])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.get_articles_for_custom_feed(filter_rules={"exclude_keywords": ["spam"]}, limit=50, offset=0)

        assert len(result) == 1

    def test_get_articles_for_custom_feed_with_min_popularity(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Popular Article", "Content", "http://url.com", 10, 10, now, now, [1])])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.get_articles_for_custom_feed(filter_rules={"min_popularity": 5}, limit=50, offset=0)

        assert len(result) == 1

    def test_get_articles_for_custom_feed_with_all_filters(self):
        now = datetime.now(timezone.utc)
        cursor = MockCursor(rows=[(1, "Python News", "Great content", "http://url.com", 10, 15, now, now, [1])])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        filter_rules = {
            "include_sources": [1],
            "exclude_sources": [2],
            "include_newspapers": [1],
            "include_keywords": ["python"],
            "exclude_keywords": ["spam"],
            "min_popularity": 10,
        }
        result = repo.get_articles_for_custom_feed(filter_rules=filter_rules, limit=50, offset=0)

        assert len(result) == 1

    def test_get_articles_for_custom_feed_empty(self):
        cursor = MockCursor(rows=[])
        factory = create_mock_connection_factory(cursor)
        repo = AggregatorRepository(connection_factory=factory)

        result = repo.get_articles_for_custom_feed(filter_rules={}, limit=50, offset=0)

        assert result == []
