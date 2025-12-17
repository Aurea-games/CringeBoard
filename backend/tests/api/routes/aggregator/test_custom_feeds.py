from __future__ import annotations

from fastapi.testclient import TestClient

CUSTOM_FEEDS_URL = "/v1/custom-feeds"
NEWSPAPERS_URL = "/v1/newspapers"
SOURCES_URL = "/v1/sources"


def register_user(client: TestClient, email: str) -> dict[str, str]:
    response = client.post(
        "/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPass1",
            "confirm_password": "StrongPass1",
        },
    )
    assert response.status_code == 201
    return response.json()


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_source(client: TestClient, token: str, name: str) -> dict:
    response = client.post(
        SOURCES_URL,
        json={"name": name, "feed_url": f"https://{name.lower()}.com/feed/"},
        headers=auth_headers(token),
    )
    assert response.status_code == 201
    return response.json()


def create_newspaper(client: TestClient, token: str, title: str, source_id: int | None = None) -> dict:
    payload = {"title": title, "description": f"Description for {title}"}
    if source_id is not None:
        payload["source_id"] = source_id
    response = client.post(
        NEWSPAPERS_URL,
        json=payload,
        headers=auth_headers(token),
    )
    assert response.status_code == 201
    return response.json()


def create_article(client: TestClient, token: str, newspaper_id: int, title: str, content: str | None = None) -> dict:
    response = client.post(
        f"{NEWSPAPERS_URL}/{newspaper_id}/articles",
        json={"title": title, "content": content},
        headers=auth_headers(token),
    )
    assert response.status_code == 201
    return response.json()


def favorite_article(client: TestClient, token: str, article_id: int) -> None:
    response = client.post(
        f"/v1/articles/{article_id}/favorite",
        headers=auth_headers(token),
    )
    assert response.status_code == 200


# ---- Authentication Tests ----


def test_create_custom_feed_requires_auth(auth_test_client: TestClient) -> None:
    response = auth_test_client.post(
        CUSTOM_FEEDS_URL,
        json={"name": "My Feed"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Authorization header missing."


def test_list_custom_feeds_requires_auth(auth_test_client: TestClient) -> None:
    response = auth_test_client.get(CUSTOM_FEEDS_URL)
    assert response.status_code == 401


def test_get_custom_feed_requires_auth(auth_test_client: TestClient) -> None:
    response = auth_test_client.get(f"{CUSTOM_FEEDS_URL}/1")
    assert response.status_code == 401


# ---- CRUD Tests ----


def test_create_and_list_custom_feeds(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "feedcreator@example.org")

    # Create first custom feed
    create_response = auth_test_client.post(
        CUSTOM_FEEDS_URL,
        json={
            "name": "Tech News",
            "description": "All tech related articles",
            "filter_rules": {
                "include_keywords": ["technology", "software"],
            },
        },
        headers=auth_headers(tokens["access_token"]),
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == "Tech News"
    assert created["description"] == "All tech related articles"
    assert created["filter_rules"]["include_keywords"] == ["technology", "software"]

    # Create second custom feed
    auth_test_client.post(
        CUSTOM_FEEDS_URL,
        json={"name": "AI Only", "filter_rules": {"include_keywords": ["AI", "machine learning"]}},
        headers=auth_headers(tokens["access_token"]),
    )

    # List custom feeds
    list_response = auth_test_client.get(
        CUSTOM_FEEDS_URL,
        headers=auth_headers(tokens["access_token"]),
    )
    assert list_response.status_code == 200
    feeds = list_response.json()
    assert len(feeds) == 2
    # Should be sorted by created_at descending
    assert feeds[0]["name"] == "AI Only"
    assert feeds[1]["name"] == "Tech News"


def test_get_custom_feed(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "feedgetter@example.org")

    create_response = auth_test_client.post(
        CUSTOM_FEEDS_URL,
        json={"name": "My Custom Feed", "description": "Test description"},
        headers=auth_headers(tokens["access_token"]),
    )
    feed_id = create_response.json()["id"]

    get_response = auth_test_client.get(
        f"{CUSTOM_FEEDS_URL}/{feed_id}",
        headers=auth_headers(tokens["access_token"]),
    )
    assert get_response.status_code == 200
    feed = get_response.json()
    assert feed["id"] == feed_id
    assert feed["name"] == "My Custom Feed"
    assert feed["description"] == "Test description"


def test_get_nonexistent_custom_feed_returns_404(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "feed404@example.org")

    response = auth_test_client.get(
        f"{CUSTOM_FEEDS_URL}/99999",
        headers=auth_headers(tokens["access_token"]),
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Custom feed not found."


def test_update_custom_feed(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "feedupdater@example.org")

    create_response = auth_test_client.post(
        CUSTOM_FEEDS_URL,
        json={"name": "Original Name", "filter_rules": {"include_keywords": ["python"]}},
        headers=auth_headers(tokens["access_token"]),
    )
    feed_id = create_response.json()["id"]

    # Update name and filter rules
    update_response = auth_test_client.patch(
        f"{CUSTOM_FEEDS_URL}/{feed_id}",
        json={
            "name": "Updated Name",
            "description": "New description",
            "filter_rules": {"include_keywords": ["python", "rust"]},
        },
        headers=auth_headers(tokens["access_token"]),
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["name"] == "Updated Name"
    assert updated["description"] == "New description"
    assert updated["filter_rules"]["include_keywords"] == ["python", "rust"]


def test_update_custom_feed_requires_at_least_one_field(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "feedpartial@example.org")

    create_response = auth_test_client.post(
        CUSTOM_FEEDS_URL,
        json={"name": "Some Feed"},
        headers=auth_headers(tokens["access_token"]),
    )
    feed_id = create_response.json()["id"]

    # Empty update should fail
    update_response = auth_test_client.patch(
        f"{CUSTOM_FEEDS_URL}/{feed_id}",
        json={},
        headers=auth_headers(tokens["access_token"]),
    )
    assert update_response.status_code == 400
    assert update_response.json()["detail"] == "At least one field must be provided for update."


def test_delete_custom_feed(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "feeddeleter@example.org")

    create_response = auth_test_client.post(
        CUSTOM_FEEDS_URL,
        json={"name": "To Be Deleted"},
        headers=auth_headers(tokens["access_token"]),
    )
    feed_id = create_response.json()["id"]

    # Delete the feed
    delete_response = auth_test_client.delete(
        f"{CUSTOM_FEEDS_URL}/{feed_id}",
        headers=auth_headers(tokens["access_token"]),
    )
    assert delete_response.status_code == 204

    # Verify it's gone
    get_response = auth_test_client.get(
        f"{CUSTOM_FEEDS_URL}/{feed_id}",
        headers=auth_headers(tokens["access_token"]),
    )
    assert get_response.status_code == 404


# ---- Permission Tests ----


def test_non_owner_cannot_view_custom_feed(auth_test_client: TestClient) -> None:
    owner_tokens = register_user(auth_test_client, "feedowner@example.org")
    other_tokens = register_user(auth_test_client, "otheruser@example.org")

    create_response = auth_test_client.post(
        CUSTOM_FEEDS_URL,
        json={"name": "Private Feed"},
        headers=auth_headers(owner_tokens["access_token"]),
    )
    feed_id = create_response.json()["id"]

    # Other user tries to view
    get_response = auth_test_client.get(
        f"{CUSTOM_FEEDS_URL}/{feed_id}",
        headers=auth_headers(other_tokens["access_token"]),
    )
    assert get_response.status_code == 403
    assert get_response.json()["detail"] == "You do not have permission to view this custom feed."


def test_non_owner_cannot_update_custom_feed(auth_test_client: TestClient) -> None:
    owner_tokens = register_user(auth_test_client, "feedowner2@example.org")
    other_tokens = register_user(auth_test_client, "otheruser2@example.org")

    create_response = auth_test_client.post(
        CUSTOM_FEEDS_URL,
        json={"name": "Owner's Feed"},
        headers=auth_headers(owner_tokens["access_token"]),
    )
    feed_id = create_response.json()["id"]

    # Other user tries to update
    update_response = auth_test_client.patch(
        f"{CUSTOM_FEEDS_URL}/{feed_id}",
        json={"name": "Hijacked Feed"},
        headers=auth_headers(other_tokens["access_token"]),
    )
    assert update_response.status_code == 403
    assert update_response.json()["detail"] == "You do not have permission to modify this custom feed."


def test_non_owner_cannot_delete_custom_feed(auth_test_client: TestClient) -> None:
    owner_tokens = register_user(auth_test_client, "feedowner3@example.org")
    other_tokens = register_user(auth_test_client, "otheruser3@example.org")

    create_response = auth_test_client.post(
        CUSTOM_FEEDS_URL,
        json={"name": "Protected Feed"},
        headers=auth_headers(owner_tokens["access_token"]),
    )
    feed_id = create_response.json()["id"]

    # Other user tries to delete
    delete_response = auth_test_client.delete(
        f"{CUSTOM_FEEDS_URL}/{feed_id}",
        headers=auth_headers(other_tokens["access_token"]),
    )
    assert delete_response.status_code == 403
    assert delete_response.json()["detail"] == "You do not have permission to delete this custom feed."


def test_users_only_see_their_own_feeds(auth_test_client: TestClient) -> None:
    user1_tokens = register_user(auth_test_client, "user1@example.org")
    user2_tokens = register_user(auth_test_client, "user2@example.org")

    # User 1 creates feeds
    auth_test_client.post(
        CUSTOM_FEEDS_URL,
        json={"name": "User1 Feed 1"},
        headers=auth_headers(user1_tokens["access_token"]),
    )
    auth_test_client.post(
        CUSTOM_FEEDS_URL,
        json={"name": "User1 Feed 2"},
        headers=auth_headers(user1_tokens["access_token"]),
    )

    # User 2 creates a feed
    auth_test_client.post(
        CUSTOM_FEEDS_URL,
        json={"name": "User2 Feed"},
        headers=auth_headers(user2_tokens["access_token"]),
    )

    # User 1 should only see their feeds
    user1_list = auth_test_client.get(
        CUSTOM_FEEDS_URL,
        headers=auth_headers(user1_tokens["access_token"]),
    )
    assert user1_list.status_code == 200
    assert len(user1_list.json()) == 2

    # User 2 should only see their feed
    user2_list = auth_test_client.get(
        CUSTOM_FEEDS_URL,
        headers=auth_headers(user2_tokens["access_token"]),
    )
    assert user2_list.status_code == 200
    assert len(user2_list.json()) == 1
    assert user2_list.json()[0]["name"] == "User2 Feed"


# ---- Filter Rules Tests ----


def test_custom_feed_filters_by_keywords(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "keyword_filter@example.org")

    # Create a newspaper and articles
    newspaper = create_newspaper(auth_test_client, tokens["access_token"], "Tech Newspaper")
    create_article(
        auth_test_client, tokens["access_token"], newspaper["id"], "Python Tutorial", "Learn python programming"
    )
    create_article(auth_test_client, tokens["access_token"], newspaper["id"], "Rust Guide", "Learn rust programming")
    create_article(auth_test_client, tokens["access_token"], newspaper["id"], "Cooking Tips", "How to cook pasta")

    # Create custom feed with keyword filter
    feed_response = auth_test_client.post(
        CUSTOM_FEEDS_URL,
        json={"name": "Programming Feed", "filter_rules": {"include_keywords": ["programming"]}},
        headers=auth_headers(tokens["access_token"]),
    )
    feed_id = feed_response.json()["id"]

    # Get feed articles
    articles_response = auth_test_client.get(
        f"{CUSTOM_FEEDS_URL}/{feed_id}/articles",
        headers=auth_headers(tokens["access_token"]),
    )
    assert articles_response.status_code == 200
    result = articles_response.json()
    assert len(result["articles"]) == 2
    article_titles = [a["title"] for a in result["articles"]]
    assert "Cooking Tips" not in article_titles
    assert "Python Tutorial" in article_titles
    assert "Rust Guide" in article_titles


def test_custom_feed_excludes_keywords(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "exclude_keyword@example.org")

    newspaper = create_newspaper(auth_test_client, tokens["access_token"], "Mixed News")
    create_article(auth_test_client, tokens["access_token"], newspaper["id"], "Good News", "Something positive")
    create_article(auth_test_client, tokens["access_token"], newspaper["id"], "Bad News", "Something negative")

    feed_response = auth_test_client.post(
        CUSTOM_FEEDS_URL,
        json={"name": "Positive Only", "filter_rules": {"exclude_keywords": ["negative"]}},
        headers=auth_headers(tokens["access_token"]),
    )
    feed_id = feed_response.json()["id"]

    articles_response = auth_test_client.get(
        f"{CUSTOM_FEEDS_URL}/{feed_id}/articles",
        headers=auth_headers(tokens["access_token"]),
    )
    assert articles_response.status_code == 200
    result = articles_response.json()
    assert len(result["articles"]) == 1
    assert result["articles"][0]["title"] == "Good News"


def test_custom_feed_filters_by_newspaper(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "newspaper_filter@example.org")

    newspaper1 = create_newspaper(auth_test_client, tokens["access_token"], "Newspaper 1")
    newspaper2 = create_newspaper(auth_test_client, tokens["access_token"], "Newspaper 2")

    create_article(auth_test_client, tokens["access_token"], newspaper1["id"], "Article in NP1")
    create_article(auth_test_client, tokens["access_token"], newspaper2["id"], "Article in NP2")

    feed_response = auth_test_client.post(
        CUSTOM_FEEDS_URL,
        json={"name": "Only NP1", "filter_rules": {"include_newspapers": [newspaper1["id"]]}},
        headers=auth_headers(tokens["access_token"]),
    )
    feed_id = feed_response.json()["id"]

    articles_response = auth_test_client.get(
        f"{CUSTOM_FEEDS_URL}/{feed_id}/articles",
        headers=auth_headers(tokens["access_token"]),
    )
    assert articles_response.status_code == 200
    result = articles_response.json()
    assert len(result["articles"]) == 1
    assert result["articles"][0]["title"] == "Article in NP1"


def test_custom_feed_filters_by_source(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "source_filter@example.org")

    source1 = create_source(auth_test_client, tokens["access_token"], "TechCrunch")
    source2 = create_source(auth_test_client, tokens["access_token"], "CookingMag")

    newspaper1 = create_newspaper(auth_test_client, tokens["access_token"], "Tech Paper", source1["id"])
    newspaper2 = create_newspaper(auth_test_client, tokens["access_token"], "Cooking Paper", source2["id"])

    create_article(auth_test_client, tokens["access_token"], newspaper1["id"], "Tech Article")
    create_article(auth_test_client, tokens["access_token"], newspaper2["id"], "Recipe Article")

    feed_response = auth_test_client.post(
        CUSTOM_FEEDS_URL,
        json={"name": "Tech Only", "filter_rules": {"include_sources": [source1["id"]]}},
        headers=auth_headers(tokens["access_token"]),
    )
    feed_id = feed_response.json()["id"]

    articles_response = auth_test_client.get(
        f"{CUSTOM_FEEDS_URL}/{feed_id}/articles",
        headers=auth_headers(tokens["access_token"]),
    )
    assert articles_response.status_code == 200
    result = articles_response.json()
    assert len(result["articles"]) == 1
    assert result["articles"][0]["title"] == "Tech Article"


def test_custom_feed_excludes_sources(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "exclude_source@example.org")

    source1 = create_source(auth_test_client, tokens["access_token"], "GoodSource")
    source2 = create_source(auth_test_client, tokens["access_token"], "BadSource")

    newspaper1 = create_newspaper(auth_test_client, tokens["access_token"], "Good Paper", source1["id"])
    newspaper2 = create_newspaper(auth_test_client, tokens["access_token"], "Bad Paper", source2["id"])

    create_article(auth_test_client, tokens["access_token"], newspaper1["id"], "Good Article")
    create_article(auth_test_client, tokens["access_token"], newspaper2["id"], "Bad Article")

    feed_response = auth_test_client.post(
        CUSTOM_FEEDS_URL,
        json={"name": "No Bad Sources", "filter_rules": {"exclude_sources": [source2["id"]]}},
        headers=auth_headers(tokens["access_token"]),
    )
    feed_id = feed_response.json()["id"]

    articles_response = auth_test_client.get(
        f"{CUSTOM_FEEDS_URL}/{feed_id}/articles",
        headers=auth_headers(tokens["access_token"]),
    )
    assert articles_response.status_code == 200
    result = articles_response.json()
    assert len(result["articles"]) == 1
    assert result["articles"][0]["title"] == "Good Article"


def test_custom_feed_filters_by_popularity(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "popularity_filter@example.org")
    user2_tokens = register_user(auth_test_client, "popularity_user2@example.org")

    newspaper = create_newspaper(auth_test_client, tokens["access_token"], "Popular Paper")
    article1 = create_article(auth_test_client, tokens["access_token"], newspaper["id"], "Popular Article")
    create_article(auth_test_client, tokens["access_token"], newspaper["id"], "Unpopular Article")

    # Favorite article1 from both users
    favorite_article(auth_test_client, tokens["access_token"], article1["id"])
    favorite_article(auth_test_client, user2_tokens["access_token"], article1["id"])

    feed_response = auth_test_client.post(
        CUSTOM_FEEDS_URL,
        json={"name": "Popular Only", "filter_rules": {"min_popularity": 2}},
        headers=auth_headers(tokens["access_token"]),
    )
    feed_id = feed_response.json()["id"]

    articles_response = auth_test_client.get(
        f"{CUSTOM_FEEDS_URL}/{feed_id}/articles",
        headers=auth_headers(tokens["access_token"]),
    )
    assert articles_response.status_code == 200
    result = articles_response.json()
    assert len(result["articles"]) == 1
    assert result["articles"][0]["title"] == "Popular Article"


def test_custom_feed_combined_filters(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "combined_filter@example.org")

    source = create_source(auth_test_client, tokens["access_token"], "TechSource")
    newspaper = create_newspaper(auth_test_client, tokens["access_token"], "Tech Paper", source["id"])

    create_article(auth_test_client, tokens["access_token"], newspaper["id"], "Python Security", "Security in python")
    create_article(auth_test_client, tokens["access_token"], newspaper["id"], "Python Basics", "Learn python basics")
    create_article(auth_test_client, tokens["access_token"], newspaper["id"], "Rust Security", "Security in rust")

    # Filter: from source AND contains "security" AND NOT "rust"
    feed_response = auth_test_client.post(
        CUSTOM_FEEDS_URL,
        json={
            "name": "Python Security Only",
            "filter_rules": {
                "include_sources": [source["id"]],
                "include_keywords": ["security"],
                "exclude_keywords": ["rust"],
            },
        },
        headers=auth_headers(tokens["access_token"]),
    )
    feed_id = feed_response.json()["id"]

    articles_response = auth_test_client.get(
        f"{CUSTOM_FEEDS_URL}/{feed_id}/articles",
        headers=auth_headers(tokens["access_token"]),
    )
    assert articles_response.status_code == 200
    result = articles_response.json()
    assert len(result["articles"]) == 1
    assert result["articles"][0]["title"] == "Python Security"


# ---- Preview Tests ----


def test_preview_custom_feed(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "preview_user@example.org")

    newspaper = create_newspaper(auth_test_client, tokens["access_token"], "Preview Paper")
    create_article(auth_test_client, tokens["access_token"], newspaper["id"], "Python Article", "Python content")
    create_article(auth_test_client, tokens["access_token"], newspaper["id"], "Java Article", "Java content")

    # Preview without saving
    preview_response = auth_test_client.post(
        f"{CUSTOM_FEEDS_URL}/preview",
        json={"include_keywords": ["python"]},
        headers=auth_headers(tokens["access_token"]),
    )
    assert preview_response.status_code == 200
    articles = preview_response.json()
    assert len(articles) == 1
    assert articles[0]["title"] == "Python Article"

    # Verify no feed was created
    list_response = auth_test_client.get(
        CUSTOM_FEEDS_URL,
        headers=auth_headers(tokens["access_token"]),
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 0


def test_preview_with_limit(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "preview_limit@example.org")

    newspaper = create_newspaper(auth_test_client, tokens["access_token"], "Many Articles Paper")
    for i in range(5):
        create_article(auth_test_client, tokens["access_token"], newspaper["id"], f"Article {i}", "Content")

    preview_response = auth_test_client.post(
        f"{CUSTOM_FEEDS_URL}/preview?limit=3",
        json={},
        headers=auth_headers(tokens["access_token"]),
    )
    assert preview_response.status_code == 200
    articles = preview_response.json()
    assert len(articles) == 3


# ---- Pagination Tests ----


def test_custom_feed_articles_pagination(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "pagination_user@example.org")

    newspaper = create_newspaper(auth_test_client, tokens["access_token"], "Pagination Paper")
    for i in range(10):
        create_article(auth_test_client, tokens["access_token"], newspaper["id"], f"Article {i}")

    feed_response = auth_test_client.post(
        CUSTOM_FEEDS_URL,
        json={"name": "All Articles"},
        headers=auth_headers(tokens["access_token"]),
    )
    feed_id = feed_response.json()["id"]

    # Get first page
    page1_response = auth_test_client.get(
        f"{CUSTOM_FEEDS_URL}/{feed_id}/articles?limit=3&offset=0",
        headers=auth_headers(tokens["access_token"]),
    )
    assert page1_response.status_code == 200
    page1 = page1_response.json()
    assert len(page1["articles"]) == 3

    # Get second page
    page2_response = auth_test_client.get(
        f"{CUSTOM_FEEDS_URL}/{feed_id}/articles?limit=3&offset=3",
        headers=auth_headers(tokens["access_token"]),
    )
    assert page2_response.status_code == 200
    page2 = page2_response.json()
    assert len(page2["articles"]) == 3

    # Ensure pages are different
    page1_ids = {a["id"] for a in page1["articles"]}
    page2_ids = {a["id"] for a in page2["articles"]}
    assert page1_ids.isdisjoint(page2_ids)


# ---- Validation Tests ----


def test_create_custom_feed_requires_name(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "noname@example.org")

    response = auth_test_client.post(
        CUSTOM_FEEDS_URL,
        json={"description": "Feed without name"},
        headers=auth_headers(tokens["access_token"]),
    )
    assert response.status_code == 422  # Validation error


def test_create_custom_feed_empty_name_fails(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "emptyname@example.org")

    response = auth_test_client.post(
        CUSTOM_FEEDS_URL,
        json={"name": "   "},
        headers=auth_headers(tokens["access_token"]),
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Name must not be empty."


def test_custom_feed_with_empty_filter_rules_returns_all_articles(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "emptyfilter@example.org")

    newspaper = create_newspaper(auth_test_client, tokens["access_token"], "Any Paper")
    create_article(auth_test_client, tokens["access_token"], newspaper["id"], "Article A")
    create_article(auth_test_client, tokens["access_token"], newspaper["id"], "Article B")

    feed_response = auth_test_client.post(
        CUSTOM_FEEDS_URL,
        json={"name": "All Articles Feed", "filter_rules": {}},
        headers=auth_headers(tokens["access_token"]),
    )
    feed_id = feed_response.json()["id"]

    articles_response = auth_test_client.get(
        f"{CUSTOM_FEEDS_URL}/{feed_id}/articles",
        headers=auth_headers(tokens["access_token"]),
    )
    assert articles_response.status_code == 200
    result = articles_response.json()
    assert len(result["articles"]) == 2
