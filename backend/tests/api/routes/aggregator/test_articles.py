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

    articles_in_first = auth_test_client.get(f"{NEWSPAPERS_URL}/{first_newspaper_id}/articles")
    assert any(article["id"] == article_id and first_newspaper_id in article["newspaper_ids"] for article in articles_in_first.json())

    articles_in_second = auth_test_client.get(f"{NEWSPAPERS_URL}/{second_newspaper_id}/articles")
    assert any(article["id"] == article_id and second_newspaper_id in article["newspaper_ids"] for article in articles_in_second.json())


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
