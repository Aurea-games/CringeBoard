"""Unit tests for AggregatorService."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.api.routes.aggregator import schemas
from app.api.routes.aggregator.services import AggregatorService
from fastapi import HTTPException


class MockAggregatorRepository:
    """Mock repository for testing AggregatorService."""

    def __init__(self):
        self.newspapers: dict[int, dict] = {}
        self.articles: dict[int, dict] = {}
        self.sources: dict[int, dict] = {}
        self.notifications: list[dict] = []
        self.custom_feeds: dict[int, dict] = {}
        self.favorites: dict[int, set[int]] = {}  # user_id -> set of article_ids
        self.read_later: dict[int, set[int]] = {}  # user_id -> set of article_ids
        self.followed_sources: dict[int, set[int]] = {}  # user_id -> set of source_ids
        self.next_newspaper_id = 1
        self.next_article_id = 1
        self.next_source_id = 1
        self.next_notification_id = 1
        self.next_custom_feed_id = 1

    def _now(self):
        return datetime.now(UTC)

    def create_newspaper(self, owner_id, title, description, source_id=None):
        nid = self.next_newspaper_id
        self.next_newspaper_id += 1
        now = self._now()
        record = {
            "id": nid,
            "title": title,
            "description": description,
            "owner_id": owner_id,
            "is_public": False,
            "public_token": None,
            "created_at": now,
            "updated_at": now,
            "source_id": source_id,
        }
        self.newspapers[nid] = record
        return record.copy()

    def get_newspaper(self, newspaper_id):
        return self.newspapers.get(newspaper_id, {}).copy() or None

    def search_newspapers(self, search=None, owner_id=None):
        results = list(self.newspapers.values())
        if owner_id:
            results = [r for r in results if r["owner_id"] == owner_id]
        if search:
            results = [r for r in results if search.lower() in r["title"].lower()]
        return [r.copy() for r in results]

    def update_newspaper(self, newspaper_id, title, description, source_id, update_source_id=False):
        record = self.newspapers.get(newspaper_id)
        if not record:
            return None
        if title:
            record["title"] = title
        if description:
            record["description"] = description
        if update_source_id:
            record["source_id"] = source_id
        record["updated_at"] = self._now()
        return record.copy()

    def delete_newspaper(self, newspaper_id):
        return self.newspapers.pop(newspaper_id, None) is not None

    def update_newspaper_publication(self, newspaper_id, is_public, public_token):
        record = self.newspapers.get(newspaper_id)
        if not record:
            return None
        record["is_public"] = is_public
        record["public_token"] = public_token
        return record.copy()

    def get_newspaper_by_token(self, token):
        for record in self.newspapers.values():
            if record.get("is_public") and record.get("public_token") == token:
                return record.copy()
        return None

    def create_article(self, owner_id, newspaper_id, title, content, url):
        aid = self.next_article_id
        self.next_article_id += 1
        now = self._now()
        record = {
            "id": aid,
            "title": title,
            "content": content,
            "url": url,
            "owner_id": owner_id,
            "popularity": 0,
            "created_at": now,
            "updated_at": now,
            "newspaper_ids": [newspaper_id],
        }
        self.articles[aid] = record
        return record.copy()

    def get_article(self, article_id):
        return self.articles.get(article_id, {}).copy() or None

    def search_articles(self, search=None, owner_id=None, newspaper_id=None, order_by_popularity=False):
        results = list(self.articles.values())
        if owner_id:
            results = [r for r in results if r["owner_id"] == owner_id]
        if newspaper_id:
            results = [r for r in results if newspaper_id in r.get("newspaper_ids", [])]
        if search:
            results = [r for r in results if search.lower() in r["title"].lower()]
        return [r.copy() for r in results]

    def update_article(self, article_id, title, content, url):
        record = self.articles.get(article_id)
        if not record:
            return None
        if title:
            record["title"] = title
        if content:
            record["content"] = content
        if url:
            record["url"] = url
        return record.copy()

    def delete_article(self, article_id):
        return self.articles.pop(article_id, None) is not None

    def assign_article_to_newspaper(self, article_id, newspaper_id):
        record = self.articles.get(article_id)
        if not record:
            return None
        if newspaper_id not in record["newspaper_ids"]:
            record["newspaper_ids"].append(newspaper_id)
        return record.copy()

    def detach_article_from_newspaper(self, article_id, newspaper_id):
        record = self.articles.get(article_id)
        if not record:
            return None
        if newspaper_id in record["newspaper_ids"]:
            record["newspaper_ids"].remove(newspaper_id)
        return record.copy()

    def get_related_articles(self, article_id, limit=10):
        return []

    def add_article_favorite(self, user_id, article_id):
        record = self.articles.get(article_id)
        if not record:
            return None
        self.favorites.setdefault(user_id, set()).add(article_id)
        record["popularity"] = len([u for u, arts in self.favorites.items() if article_id in arts])
        return record.copy()

    def remove_article_favorite(self, user_id, article_id):
        record = self.articles.get(article_id)
        if not record:
            return None
        self.favorites.setdefault(user_id, set()).discard(article_id)
        return record.copy()

    def list_favorite_articles(self, user_id):
        fav_ids = self.favorites.get(user_id, set())
        return [self.articles[aid].copy() for aid in fav_ids if aid in self.articles]

    def add_read_later(self, user_id, article_id):
        record = self.articles.get(article_id)
        if not record:
            return None
        self.read_later.setdefault(user_id, set()).add(article_id)
        return record.copy()

    def remove_read_later(self, user_id, article_id):
        record = self.articles.get(article_id)
        if not record:
            return None
        self.read_later.setdefault(user_id, set()).discard(article_id)
        return record.copy()

    def list_read_later_articles(self, user_id):
        rl_ids = self.read_later.get(user_id, set())
        return [self.articles[aid].copy() for aid in rl_ids if aid in self.articles]

    def create_source(self, name, feed_url, description, status="active"):
        sid = self.next_source_id
        self.next_source_id += 1
        now = self._now()
        record = {
            "id": sid,
            "name": name,
            "feed_url": feed_url,
            "description": description,
            "status": status,
            "created_at": now,
            "updated_at": now,
            "is_followed": False,
        }
        self.sources[sid] = record
        return record.copy()

    def get_source(self, source_id, follower_id=None):
        record = self.sources.get(source_id)
        if not record:
            return None
        result = record.copy()
        if follower_id:
            result["is_followed"] = source_id in self.followed_sources.get(follower_id, set())
        return result

    def list_sources(self, search=None, status=None, follower_id=None):
        results = list(self.sources.values())
        if status:
            results = [r for r in results if r.get("status") == status]
        if search:
            results = [r for r in results if search.lower() in r["name"].lower()]
        return [r.copy() for r in results]

    def update_source(self, source_id, name, feed_url, description, status):
        record = self.sources.get(source_id)
        if not record:
            return None
        if name:
            record["name"] = name
        if feed_url:
            record["feed_url"] = feed_url
        if description:
            record["description"] = description
        if status:
            record["status"] = status
        return record.copy()

    def follow_source(self, user_id, source_id):
        if source_id not in self.sources:
            return None
        self.followed_sources.setdefault(user_id, set()).add(source_id)
        return self.get_source(source_id, follower_id=user_id)

    def unfollow_source(self, user_id, source_id):
        if source_id not in self.sources:
            return None
        self.followed_sources.setdefault(user_id, set()).discard(source_id)
        return self.get_source(source_id, follower_id=user_id)

    def list_followed_sources(self, user_id):
        followed_ids = self.followed_sources.get(user_id, set())
        return [self.sources[sid].copy() for sid in followed_ids if sid in self.sources]

    def create_notifications_for_source_followers(self, source_id, message, article_id=None, newspaper_id=None):
        count = 0
        for user_id, followed in self.followed_sources.items():
            if source_id in followed:
                self.notifications.append(
                    {
                        "id": self.next_notification_id,
                        "user_id": user_id,
                        "source_id": source_id,
                        "article_id": article_id,
                        "newspaper_id": newspaper_id,
                        "message": message,
                        "is_read": False,
                        "created_at": self._now(),
                    }
                )
                self.next_notification_id += 1
                count += 1
        return count

    def list_notifications(self, user_id, include_read=False):
        results = [n for n in self.notifications if n["user_id"] == user_id]
        if not include_read:
            results = [n for n in results if not n["is_read"]]
        return results

    def mark_notification_read(self, user_id, notification_id):
        for n in self.notifications:
            if n["id"] == notification_id and n["user_id"] == user_id:
                n["is_read"] = True
                return n.copy()
        return None

    def create_custom_feed(self, owner_id, name, description, filter_rules):
        cfid = self.next_custom_feed_id
        self.next_custom_feed_id += 1
        now = self._now()
        record = {
            "id": cfid,
            "owner_id": owner_id,
            "name": name,
            "description": description,
            "filter_rules": filter_rules,
            "created_at": now,
            "updated_at": now,
        }
        self.custom_feeds[cfid] = record
        return record.copy()

    def get_custom_feed(self, custom_feed_id):
        return self.custom_feeds.get(custom_feed_id, {}).copy() or None

    def list_custom_feeds(self, owner_id):
        return [r.copy() for r in self.custom_feeds.values() if r["owner_id"] == owner_id]

    def update_custom_feed(self, custom_feed_id, name, description, filter_rules):
        record = self.custom_feeds.get(custom_feed_id)
        if not record:
            return None
        if name:
            record["name"] = name
        if description:
            record["description"] = description
        if filter_rules:
            record["filter_rules"] = filter_rules
        return record.copy()

    def delete_custom_feed(self, custom_feed_id):
        return self.custom_feeds.pop(custom_feed_id, None) is not None

    def get_articles_for_custom_feed(self, filter_rules, limit=50, offset=0):
        return list(self.articles.values())[offset : offset + limit]


class MockAuthRepository:
    """Mock auth repository for testing."""

    def __init__(self):
        self.users = {"user@test.com": 1, "other@test.com": 2}

    def get_user_id(self, email):
        return self.users.get(email)


class TestAggregatorServiceNewspapers:
    """Test newspaper-related service methods."""

    def test_list_newspapers(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        repo.create_newspaper(1, "Test Paper", "Description")

        result = service.list_newspapers()

        assert len(result) == 1
        assert result[0].title == "Test Paper"

    def test_list_newspapers_with_search(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        repo.create_newspaper(1, "Python News", "Description")
        repo.create_newspaper(1, "JavaScript News", "Description")

        result = service.list_newspapers(search="Python")

        assert len(result) == 1
        assert result[0].title == "Python News"

    def test_list_newspapers_with_owner_email(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        repo.create_newspaper(1, "User1 Paper", "Description")
        repo.create_newspaper(2, "User2 Paper", "Description")

        result = service.list_newspapers(owner_email="user@test.com")

        assert len(result) == 1

    def test_list_newspapers_owner_not_found_returns_empty(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        result = service.list_newspapers(owner_email="nonexistent@test.com")

        assert result == []

    def test_create_newspaper_success(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        payload = schemas.NewspaperCreate(title="New Paper", description="A great paper")
        result = service.create_newspaper("user@test.com", payload)

        assert result.title == "New Paper"
        assert result.description == "A great paper"

    def test_create_newspaper_empty_title_raises(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        payload = schemas.NewspaperCreate(title="   ", description="Desc")

        with pytest.raises(HTTPException) as exc_info:
            service.create_newspaper("user@test.com", payload)

        assert exc_info.value.status_code == 400
        assert "Title must not be empty" in exc_info.value.detail

    def test_create_newspaper_with_source(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        source = repo.create_source("Test Source", "http://feed.url", "Desc")
        payload = schemas.NewspaperCreate(title="New Paper", source_id=source["id"])

        result = service.create_newspaper("user@test.com", payload)

        assert result.source_id == source["id"]

    def test_create_newspaper_source_not_found_raises(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        payload = schemas.NewspaperCreate(title="New Paper", source_id=999)

        with pytest.raises(HTTPException) as exc_info:
            service.create_newspaper("user@test.com", payload)

        assert exc_info.value.status_code == 404

    def test_get_newspaper_success(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        newspaper = repo.create_newspaper(1, "Test Paper", "Description")

        result = service.get_newspaper(newspaper["id"])

        assert result.id == newspaper["id"]

    def test_get_newspaper_not_found_raises(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        with pytest.raises(HTTPException) as exc_info:
            service.get_newspaper(999)

        assert exc_info.value.status_code == 404

    def test_update_newspaper_success(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        newspaper = repo.create_newspaper(1, "Old Title", "Old Desc")
        payload = schemas.NewspaperUpdate(title="New Title")

        result = service.update_newspaper(newspaper["id"], "user@test.com", payload)

        assert result.title == "New Title"

    def test_update_newspaper_not_found_raises(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        payload = schemas.NewspaperUpdate(title="New Title")

        with pytest.raises(HTTPException) as exc_info:
            service.update_newspaper(999, "user@test.com", payload)

        assert exc_info.value.status_code == 404

    def test_update_newspaper_not_owner_raises(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        newspaper = repo.create_newspaper(1, "Title", "Desc")
        payload = schemas.NewspaperUpdate(title="New Title")

        with pytest.raises(HTTPException) as exc_info:
            service.update_newspaper(newspaper["id"], "other@test.com", payload)

        assert exc_info.value.status_code == 403

    def test_update_newspaper_empty_payload_raises(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        newspaper = repo.create_newspaper(1, "Title", "Desc")
        payload = schemas.NewspaperUpdate()

        with pytest.raises(HTTPException) as exc_info:
            service.update_newspaper(newspaper["id"], "user@test.com", payload)

        assert exc_info.value.status_code == 400

    def test_update_newspaper_empty_title_raises(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        newspaper = repo.create_newspaper(1, "Title", "Desc")
        payload = schemas.NewspaperUpdate(title="   ")

        with pytest.raises(HTTPException) as exc_info:
            service.update_newspaper(newspaper["id"], "user@test.com", payload)

        assert exc_info.value.status_code == 400

    def test_delete_newspaper_success(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        newspaper = repo.create_newspaper(1, "Title", "Desc")

        service.delete_newspaper(newspaper["id"], "user@test.com")

        assert newspaper["id"] not in repo.newspapers

    def test_delete_newspaper_not_owner_raises(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        newspaper = repo.create_newspaper(1, "Title", "Desc")

        with pytest.raises(HTTPException) as exc_info:
            service.delete_newspaper(newspaper["id"], "other@test.com")

        assert exc_info.value.status_code == 403

    def test_share_newspaper_make_public(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        newspaper = repo.create_newspaper(1, "Title", "Desc")

        result = service.share_newspaper(newspaper["id"], "user@test.com", make_public=True)

        assert result.is_public is True
        assert result.public_token is not None

    def test_share_newspaper_make_private(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        newspaper = repo.create_newspaper(1, "Title", "Desc")
        repo.update_newspaper_publication(newspaper["id"], True, "token123")

        result = service.share_newspaper(newspaper["id"], "user@test.com", make_public=False)

        assert result.is_public is False

    def test_get_public_newspaper(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        newspaper = repo.create_newspaper(1, "Public Paper", "Desc")
        repo.update_newspaper_publication(newspaper["id"], True, "public-token")

        result = service.get_public_newspaper("public-token")

        assert result.title == "Public Paper"

    def test_get_public_newspaper_not_found(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        with pytest.raises(HTTPException) as exc_info:
            service.get_public_newspaper("invalid-token")

        assert exc_info.value.status_code == 404


class TestAggregatorServiceArticles:
    """Test article-related service methods."""

    def test_create_article_success(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        newspaper = repo.create_newspaper(1, "Paper", "Desc")
        payload = schemas.ArticleCreate(title="Article", content="Content", url="http://example.com")

        result = service.create_article(newspaper["id"], "user@test.com", payload)

        assert result.title == "Article"

    def test_create_article_empty_title_raises(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        newspaper = repo.create_newspaper(1, "Paper", "Desc")
        payload = schemas.ArticleCreate(title="   ", content="Content")

        with pytest.raises(HTTPException) as exc_info:
            service.create_article(newspaper["id"], "user@test.com", payload)

        assert exc_info.value.status_code == 400

    def test_create_article_newspaper_not_found_raises(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        payload = schemas.ArticleCreate(title="Article", content="Content")

        with pytest.raises(HTTPException) as exc_info:
            service.create_article(999, "user@test.com", payload)

        assert exc_info.value.status_code == 404

    def test_get_article_success(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        newspaper = repo.create_newspaper(1, "Paper", "Desc")
        article = repo.create_article(1, newspaper["id"], "Article", "Content", None)

        result = service.get_article(article["id"])

        assert result.id == article["id"]

    def test_get_article_not_found_raises(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        with pytest.raises(HTTPException) as exc_info:
            service.get_article(999)

        assert exc_info.value.status_code == 404

    def test_update_article_success(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        newspaper = repo.create_newspaper(1, "Paper", "Desc")
        article = repo.create_article(1, newspaper["id"], "Article", "Content", None)
        payload = schemas.ArticleUpdate(title="New Title")

        result = service.update_article(article["id"], "user@test.com", payload)

        assert result.title == "New Title"

    def test_update_article_empty_payload_raises(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        newspaper = repo.create_newspaper(1, "Paper", "Desc")
        article = repo.create_article(1, newspaper["id"], "Article", "Content", None)
        payload = schemas.ArticleUpdate()

        with pytest.raises(HTTPException) as exc_info:
            service.update_article(article["id"], "user@test.com", payload)

        assert exc_info.value.status_code == 400

    def test_delete_article_success(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        newspaper = repo.create_newspaper(1, "Paper", "Desc")
        article = repo.create_article(1, newspaper["id"], "Article", "Content", None)

        service.delete_article(article["id"], "user@test.com")

        assert article["id"] not in repo.articles

    def test_favorite_article(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        newspaper = repo.create_newspaper(1, "Paper", "Desc")
        article = repo.create_article(1, newspaper["id"], "Article", "Content", None)

        result = service.favorite_article(article["id"], "user@test.com")

        assert result.id == article["id"]

    def test_unfavorite_article(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        newspaper = repo.create_newspaper(1, "Paper", "Desc")
        article = repo.create_article(1, newspaper["id"], "Article", "Content", None)
        repo.add_article_favorite(1, article["id"])

        result = service.unfavorite_article(article["id"], "user@test.com")

        assert result.id == article["id"]

    def test_save_article_for_later(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        newspaper = repo.create_newspaper(1, "Paper", "Desc")
        article = repo.create_article(1, newspaper["id"], "Article", "Content", None)

        result = service.save_article_for_later(article["id"], "user@test.com")

        assert result.id == article["id"]

    def test_remove_article_from_read_later(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        newspaper = repo.create_newspaper(1, "Paper", "Desc")
        article = repo.create_article(1, newspaper["id"], "Article", "Content", None)
        repo.add_read_later(1, article["id"])

        result = service.remove_article_from_read_later(article["id"], "user@test.com")

        assert result.id == article["id"]

    def test_list_related_articles(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        newspaper = repo.create_newspaper(1, "Paper", "Desc")
        article = repo.create_article(1, newspaper["id"], "Article", "Content", None)

        result = service.list_related_articles(article["id"])

        assert result == []

    def test_list_related_articles_not_found_raises(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        with pytest.raises(HTTPException) as exc_info:
            service.list_related_articles(999)

        assert exc_info.value.status_code == 404


class TestAggregatorServiceSources:
    """Test source-related service methods."""

    def test_list_sources(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        repo.create_source("Source 1", "http://feed1.com", "Desc")

        result = service.list_sources()

        assert len(result) == 1

    def test_create_source_success(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        payload = schemas.SourceCreate(name="New Source", feed_url="http://feed.url", description="Desc")

        result = service.create_source(payload)

        assert result.name == "New Source"

    def test_create_source_empty_name_raises(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        payload = schemas.SourceCreate(name="   ")

        with pytest.raises(HTTPException) as exc_info:
            service.create_source(payload)

        assert exc_info.value.status_code == 400

    def test_get_source_success(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        source = repo.create_source("Source", "http://feed.url", "Desc")

        result = service.get_source(source["id"])

        assert result.id == source["id"]

    def test_get_source_not_found_raises(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        with pytest.raises(HTTPException) as exc_info:
            service.get_source(999)

        assert exc_info.value.status_code == 404

    def test_update_source_success(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        source = repo.create_source("Source", "http://feed.url", "Desc")
        payload = schemas.SourceUpdate(name="New Name")

        result = service.update_source(source["id"], payload)

        assert result.name == "New Name"

    def test_update_source_empty_payload_raises(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        source = repo.create_source("Source", "http://feed.url", "Desc")
        payload = schemas.SourceUpdate()

        with pytest.raises(HTTPException) as exc_info:
            service.update_source(source["id"], payload)

        assert exc_info.value.status_code == 400

    def test_update_source_empty_name_raises(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        source = repo.create_source("Source", "http://feed.url", "Desc")
        payload = schemas.SourceUpdate(name="   ")

        with pytest.raises(HTTPException) as exc_info:
            service.update_source(source["id"], payload)

        assert exc_info.value.status_code == 400

    def test_follow_source(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        source = repo.create_source("Source", "http://feed.url", "Desc")

        result = service.follow_source(source["id"], "user@test.com")

        assert result.is_followed is True

    def test_unfollow_source(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        source = repo.create_source("Source", "http://feed.url", "Desc")
        repo.follow_source(1, source["id"])

        result = service.unfollow_source(source["id"], "user@test.com")

        assert result.is_followed is False


class TestAggregatorServiceNotifications:
    """Test notification-related service methods."""

    def test_list_notifications(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        source = repo.create_source("Source", "http://feed.url", "Desc")
        repo.follow_source(1, source["id"])
        repo.create_notifications_for_source_followers(source["id"], "Test message")

        result = service.list_notifications("user@test.com")

        assert len(result) == 1

    def test_mark_notification_read(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        source = repo.create_source("Source", "http://feed.url", "Desc")
        repo.follow_source(1, source["id"])
        repo.create_notifications_for_source_followers(source["id"], "Test message")

        notification = repo.notifications[0]
        result = service.mark_notification_read(notification["id"], "user@test.com")

        assert result.is_read is True

    def test_mark_notification_read_not_found_raises(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        with pytest.raises(HTTPException) as exc_info:
            service.mark_notification_read(999, "user@test.com")

        assert exc_info.value.status_code == 404


class TestAggregatorServiceCustomFeeds:
    """Test custom feed-related service methods."""

    def test_create_custom_feed_success(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        filter_rules = schemas.CustomFeedFilterRules(include_keywords=["python"])
        payload = schemas.CustomFeedCreate(name="My Feed", description="Desc", filter_rules=filter_rules)

        result = service.create_custom_feed("user@test.com", payload)

        assert result.name == "My Feed"

    def test_create_custom_feed_empty_name_raises(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        filter_rules = schemas.CustomFeedFilterRules()
        payload = schemas.CustomFeedCreate(name="   ", filter_rules=filter_rules)

        with pytest.raises(HTTPException) as exc_info:
            service.create_custom_feed("user@test.com", payload)

        assert exc_info.value.status_code == 400

    def test_get_custom_feed_success(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        feed = repo.create_custom_feed(1, "Feed", "Desc", {})

        result = service.get_custom_feed(feed["id"], "user@test.com")

        assert result.id == feed["id"]

    def test_get_custom_feed_not_found_raises(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        with pytest.raises(HTTPException) as exc_info:
            service.get_custom_feed(999, "user@test.com")

        assert exc_info.value.status_code == 404

    def test_get_custom_feed_not_owner_raises(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        feed = repo.create_custom_feed(1, "Feed", "Desc", {})

        with pytest.raises(HTTPException) as exc_info:
            service.get_custom_feed(feed["id"], "other@test.com")

        assert exc_info.value.status_code == 403

    def test_update_custom_feed_success(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        feed = repo.create_custom_feed(1, "Feed", "Desc", {})
        payload = schemas.CustomFeedUpdate(name="New Name")

        result = service.update_custom_feed(feed["id"], "user@test.com", payload)

        assert result.name == "New Name"

    def test_update_custom_feed_empty_payload_raises(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        feed = repo.create_custom_feed(1, "Feed", "Desc", {})
        payload = schemas.CustomFeedUpdate()

        with pytest.raises(HTTPException) as exc_info:
            service.update_custom_feed(feed["id"], "user@test.com", payload)

        assert exc_info.value.status_code == 400

    def test_update_custom_feed_empty_name_raises(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        feed = repo.create_custom_feed(1, "Feed", "Desc", {})
        payload = schemas.CustomFeedUpdate(name="   ")

        with pytest.raises(HTTPException) as exc_info:
            service.update_custom_feed(feed["id"], "user@test.com", payload)

        assert exc_info.value.status_code == 400

    def test_delete_custom_feed_success(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        feed = repo.create_custom_feed(1, "Feed", "Desc", {})

        service.delete_custom_feed(feed["id"], "user@test.com")

        assert feed["id"] not in repo.custom_feeds

    def test_get_custom_feed_articles(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        feed = repo.create_custom_feed(1, "Feed", "Desc", {"include_keywords": ["python"]})

        result = service.get_custom_feed_articles(feed["id"], "user@test.com")

        assert result.name == "Feed"

    def test_preview_custom_feed(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        filter_rules = schemas.CustomFeedFilterRules(include_keywords=["python"])

        result = service.preview_custom_feed("user@test.com", filter_rules)

        assert isinstance(result, list)


class TestAggregatorServiceHelpers:
    """Test helper methods."""

    def test_get_user_id_not_found_raises(self):
        repo = MockAggregatorRepository()
        auth_repo = MockAuthRepository()
        service = AggregatorService(repo, auth_repo)

        with pytest.raises(HTTPException) as exc_info:
            service.get_user_id("nonexistent@test.com")

        assert exc_info.value.status_code == 404

    def test_ensure_ownership_success(self):
        # Should not raise
        AggregatorService.ensure_ownership(1, 1, "test action")

    def test_ensure_ownership_fails(self):
        with pytest.raises(HTTPException) as exc_info:
            AggregatorService.ensure_ownership(1, 2, "test action")

        assert exc_info.value.status_code == 403
