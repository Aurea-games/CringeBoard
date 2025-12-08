from __future__ import annotations

from fastapi.testclient import TestClient

NEWSPAPERS_URL = "/v1/newspapers"
ARTICLES_URL = "/v1/articles"


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


def create_newspaper(client: TestClient, token: str, title: str = "Daily News") -> int:
    response = client.post(
        NEWSPAPERS_URL,
        json={"title": title, "description": "General updates."},
        headers=auth_headers(token),
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_non_owner_cannot_create_article(auth_test_client: TestClient) -> None:
    owner_tokens = register_user(auth_test_client, "owner@example.org")
    other_tokens = register_user(auth_test_client, "visitor@example.org")
    newspaper_id = create_newspaper(auth_test_client, owner_tokens["access_token"])

    response = auth_test_client.post(
        f"{NEWSPAPERS_URL}/{newspaper_id}/articles",
        json={
            "title": "Unauthorized Story",
            "content": "Should not be allowed.",
        },
        headers=auth_headers(other_tokens["access_token"]),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "You do not have permission to add articles to this newspaper."


def test_article_owner_can_manage_article(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "author@example.org")
    newspaper_id = create_newspaper(auth_test_client, tokens["access_token"])

    create_response = auth_test_client.post(
        f"{NEWSPAPERS_URL}/{newspaper_id}/articles",
        json={
            "title": "Launch Event",
            "content": "Covering the launch event.",
            "url": "https://example.org/articles/launch",
        },
        headers=auth_headers(tokens["access_token"]),
    )
    assert create_response.status_code == 201
    article = create_response.json()
    article_id = article["id"]
    assert article["newspaper_ids"] == [newspaper_id]
    assert article["popularity"] == 0

    list_response = auth_test_client.get(f"{NEWSPAPERS_URL}/{newspaper_id}/articles")
    assert list_response.status_code == 200
    articles = list_response.json()
    assert len(articles) == 1
    assert articles[0]["id"] == article_id
    assert newspaper_id in articles[0]["newspaper_ids"]

    update_response = auth_test_client.patch(
        f"{ARTICLES_URL}/{article_id}",
        json={"title": "Updated Launch Event", "content": "Updated coverage."},
        headers=auth_headers(tokens["access_token"]),
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["title"] == "Updated Launch Event"
    assert updated["content"] == "Updated coverage."
    assert newspaper_id in updated["newspaper_ids"]
    assert updated["popularity"] == 0

    delete_response = auth_test_client.delete(
        f"{ARTICLES_URL}/{article_id}",
        headers=auth_headers(tokens["access_token"]),
    )
    assert delete_response.status_code == 204

    get_response = auth_test_client.get(f"{ARTICLES_URL}/{article_id}")
    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "Article not found."


def test_non_owner_cannot_modify_article(auth_test_client: TestClient) -> None:
    owner_tokens = register_user(auth_test_client, "writer@example.org")
    other_tokens = register_user(auth_test_client, "reader@example.org")
    newspaper_id = create_newspaper(auth_test_client, owner_tokens["access_token"])

    article_response = auth_test_client.post(
        f"{NEWSPAPERS_URL}/{newspaper_id}/articles",
        json={
            "title": "Private Draft",
            "content": "Should remain private.",
        },
        headers=auth_headers(owner_tokens["access_token"]),
    )
    article_id = article_response.json()["id"]

    update_response = auth_test_client.patch(
        f"{ARTICLES_URL}/{article_id}",
        json={"title": "Leaked Draft"},
        headers=auth_headers(other_tokens["access_token"]),
    )
    assert update_response.status_code == 403
    assert update_response.json()["detail"] == "You do not have permission to modify this article."

    delete_response = auth_test_client.delete(
        f"{ARTICLES_URL}/{article_id}",
        headers=auth_headers(other_tokens["access_token"]),
    )
    assert delete_response.status_code == 403
    assert delete_response.json()["detail"] == "You do not have permission to delete this article."


def test_search_articles_endpoint_supports_filters(auth_test_client: TestClient) -> None:
    owner_tokens = register_user(auth_test_client, "collector@example.org")

    tech_newspaper = create_newspaper(auth_test_client, owner_tokens["access_token"], title="Tech Daily")
    science_newspaper = create_newspaper(auth_test_client, owner_tokens["access_token"], title="Science Weekly")

    article_one = auth_test_client.post(
        f"{NEWSPAPERS_URL}/{tech_newspaper}/articles",
        json={
            "title": "Launch Event",
            "content": "Covering the tech launch.",
        },
        headers=auth_headers(owner_tokens["access_token"]),
    ).json()

    auth_test_client.post(
        f"{NEWSPAPERS_URL}/{science_newspaper}/articles",
        json={
            "title": "Research Update",
            "content": "Science news.",
        },
        headers=auth_headers(owner_tokens["access_token"]),
    )

    # Attach one article to an extra newspaper to verify filtering by newspaper_id
    auth_test_client.post(
        f"{NEWSPAPERS_URL}/{science_newspaper}/articles/{article_one['id']}",
        headers=auth_headers(owner_tokens["access_token"]),
    )

    search_response = auth_test_client.get(ARTICLES_URL, params={"q": "Launch"})
    assert search_response.status_code == 200
    assert len(search_response.json()) == 1
    assert search_response.json()[0]["title"] == "Launch Event"

    owner_response = auth_test_client.get(ARTICLES_URL, params={"owner_email": "collector@example.org"})
    assert owner_response.status_code == 200
    assert {article["title"] for article in owner_response.json()} == {"Launch Event", "Research Update"}

    filtered_by_newspaper = auth_test_client.get(ARTICLES_URL, params={"newspaper_id": science_newspaper})
    assert filtered_by_newspaper.status_code == 200
    titles = {article["title"] for article in filtered_by_newspaper.json()}
    assert titles == {"Launch Event", "Research Update"}


def test_owner_can_attach_existing_article_to_newspaper(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "publisher@example.org")
    first_newspaper_id = create_newspaper(auth_test_client, tokens["access_token"], title="Daily Tech")
    second_newspaper_id = create_newspaper(auth_test_client, tokens["access_token"], title="Weekly Science")

    create_response = auth_test_client.post(
        f"{NEWSPAPERS_URL}/{first_newspaper_id}/articles",
        json={
            "title": "Quantum Breakthrough",
            "content": "Scientists reveal new findings.",
        },
        headers=auth_headers(tokens["access_token"]),
    )
    article_id = create_response.json()["id"]

    attach_response = auth_test_client.post(
        f"{NEWSPAPERS_URL}/{second_newspaper_id}/articles/{article_id}",
        headers=auth_headers(tokens["access_token"]),
    )

    assert attach_response.status_code == 200
    updated_article = attach_response.json()
    assert updated_article["id"] == article_id
    assert updated_article["newspaper_ids"] == sorted([first_newspaper_id, second_newspaper_id])


def test_users_can_favorite_articles(auth_test_client: TestClient) -> None:
    author_tokens = register_user(auth_test_client, "author2@example.org")
    fan_tokens = register_user(auth_test_client, "fan@example.org")
    second_fan_tokens = register_user(auth_test_client, "fan2@example.org")

    newspaper_id = create_newspaper(auth_test_client, author_tokens["access_token"])
    article = auth_test_client.post(
        f"{NEWSPAPERS_URL}/{newspaper_id}/articles",
        json={
            "title": "Community Update",
            "content": "Weekly digest.",
        },
        headers=auth_headers(author_tokens["access_token"]),
    ).json()
    article_id = article["id"]
    assert article["popularity"] == 0

    first_favorite = auth_test_client.post(
        f"{ARTICLES_URL}/{article_id}/favorite",
        headers=auth_headers(fan_tokens["access_token"]),
    )
    assert first_favorite.status_code == 200
    assert first_favorite.json()["popularity"] == 1

    duplicate_favorite = auth_test_client.post(
        f"{ARTICLES_URL}/{article_id}/favorite",
        headers=auth_headers(fan_tokens["access_token"]),
    )
    assert duplicate_favorite.status_code == 200
    assert duplicate_favorite.json()["popularity"] == 1

    second_favorite = auth_test_client.post(
        f"{ARTICLES_URL}/{article_id}/favorite",
        headers=auth_headers(second_fan_tokens["access_token"]),
    )
    assert second_favorite.status_code == 200
    assert second_favorite.json()["popularity"] == 2

    refreshed = auth_test_client.get(f"{ARTICLES_URL}/{article_id}")
    assert refreshed.status_code == 200
    assert refreshed.json()["popularity"] == 2


def test_list_articles_sorted_by_popularity(auth_test_client: TestClient) -> None:
    author_tokens = register_user(auth_test_client, "author3@example.org")
    fan_one = register_user(auth_test_client, "fan3@example.org")
    fan_two = register_user(auth_test_client, "fan4@example.org")

    newspaper_id = create_newspaper(auth_test_client, author_tokens["access_token"])
    auth_test_client.post(
        f"{NEWSPAPERS_URL}/{newspaper_id}/articles",
        json={"title": "Low", "content": "low"},
        headers=auth_headers(author_tokens["access_token"]),
    ).json()
    mid_pop = auth_test_client.post(
        f"{NEWSPAPERS_URL}/{newspaper_id}/articles",
        json={"title": "Mid", "content": "mid"},
        headers=auth_headers(author_tokens["access_token"]),
    ).json()
    high_pop = auth_test_client.post(
        f"{NEWSPAPERS_URL}/{newspaper_id}/articles",
        json={"title": "High", "content": "high"},
        headers=auth_headers(author_tokens["access_token"]),
    ).json()

    # favorite counts: low=0, mid=1, high=2
    auth_test_client.post(
        f"{ARTICLES_URL}/{mid_pop['id']}/favorite",
        headers=auth_headers(fan_one["access_token"]),
    )
    auth_test_client.post(
        f"{ARTICLES_URL}/{high_pop['id']}/favorite",
        headers=auth_headers(fan_one["access_token"]),
    )
    auth_test_client.post(
        f"{ARTICLES_URL}/{high_pop['id']}/favorite",
        headers=auth_headers(fan_two["access_token"]),
    )

    popular_response = auth_test_client.get(f"{ARTICLES_URL}/popular")
    assert popular_response.status_code == 200
    titles_order = [article["title"] for article in popular_response.json()]
    assert titles_order[:3] == ["High", "Mid", "Low"]


def test_non_owner_can_attach_article_to_newspaper(auth_test_client: TestClient) -> None:
    owner_tokens = register_user(auth_test_client, "owner2@example.org")
    other_tokens = register_user(auth_test_client, "other2@example.org")

    owner_newspaper_id = create_newspaper(auth_test_client, owner_tokens["access_token"], title="Owner Paper")
    other_newspaper_id = create_newspaper(auth_test_client, other_tokens["access_token"], title="Other Paper")

    create_response = auth_test_client.post(
        f"{NEWSPAPERS_URL}/{owner_newspaper_id}/articles",
        json={
            "title": "Exclusive Story",
            "content": "Only for owner.",
        },
        headers=auth_headers(owner_tokens["access_token"]),
    )
    article_id = create_response.json()["id"]
    assert create_response.json()["newspaper_ids"] == [owner_newspaper_id]

    attach_response = auth_test_client.post(
        f"{NEWSPAPERS_URL}/{other_newspaper_id}/articles/{article_id}",
        headers=auth_headers(other_tokens["access_token"]),
    )

    assert attach_response.status_code == 200
    attached = attach_response.json()
    assert other_newspaper_id in attached["newspaper_ids"]


def test_user_can_manage_favorites_collection(auth_test_client: TestClient) -> None:
    author_tokens = register_user(auth_test_client, "favorites-author@example.org")
    fan_tokens = register_user(auth_test_client, "favorites-fan@example.org")

    newspaper_id = create_newspaper(auth_test_client, author_tokens["access_token"], title="Favorites Daily")
    article = auth_test_client.post(
        f"{NEWSPAPERS_URL}/{newspaper_id}/articles",
        json={
            "title": "Favorite Me",
            "content": "Save this article.",
        },
        headers=auth_headers(author_tokens["access_token"]),
    ).json()
    article_id = article["id"]

    favorite_response = auth_test_client.post(
        "/v1/me/favorites",
        json={"articleId": article_id},
        headers=auth_headers(fan_tokens["access_token"]),
    )
    assert favorite_response.status_code == 201
    assert favorite_response.json()["popularity"] == 1

    favorites_list = auth_test_client.get(
        "/v1/me/favorites",
        headers=auth_headers(fan_tokens["access_token"]),
    )
    assert favorites_list.status_code == 200
    favorites = favorites_list.json()
    assert len(favorites) == 1
    assert favorites[0]["id"] == article_id

    delete_response = auth_test_client.delete(
        f"/v1/me/favorites/{article_id}",
        headers=auth_headers(fan_tokens["access_token"]),
    )
    assert delete_response.status_code == 204

    empty_list = auth_test_client.get(
        "/v1/me/favorites",
        headers=auth_headers(fan_tokens["access_token"]),
    )
    assert empty_list.status_code == 200
    assert empty_list.json() == []

    refreshed = auth_test_client.get(f"{ARTICLES_URL}/{article_id}")
    assert refreshed.status_code == 200
    assert refreshed.json()["popularity"] == 0


def test_user_can_manage_read_later_list(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "reader@example.org")
    newspaper_id = create_newspaper(auth_test_client, tokens["access_token"], title="Read Later Times")
    article = auth_test_client.post(
        f"{NEWSPAPERS_URL}/{newspaper_id}/articles",
        json={
            "title": "To Read Soon",
            "content": "Mark for later reading.",
        },
        headers=auth_headers(tokens["access_token"]),
    ).json()

    add_response = auth_test_client.post(
        "/v1/me/read-later",
        json={"articleId": article["id"]},
        headers=auth_headers(tokens["access_token"]),
    )
    assert add_response.status_code == 201
    assert add_response.json()["id"] == article["id"]

    list_response = auth_test_client.get(
        "/v1/me/read-later",
        headers=auth_headers(tokens["access_token"]),
    )
    assert list_response.status_code == 200
    saved = list_response.json()
    assert len(saved) == 1
    assert saved[0]["id"] == article["id"]

    remove_response = auth_test_client.delete(
        f"/v1/me/read-later/{article['id']}",
        headers=auth_headers(tokens["access_token"]),
    )
    assert remove_response.status_code == 204

    confirm_empty = auth_test_client.get(
        "/v1/me/read-later",
        headers=auth_headers(tokens["access_token"]),
    )
    assert confirm_empty.status_code == 200
    assert confirm_empty.json() == []
