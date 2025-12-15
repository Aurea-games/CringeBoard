from __future__ import annotations

from fastapi.testclient import TestClient

NEWSPAPERS_URL = "/v1/newspapers"
PUBLIC_URL = "/v1/public/newspapers"


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


def test_create_newspaper_requires_auth(auth_test_client: TestClient) -> None:
    response = auth_test_client.post(
        NEWSPAPERS_URL,
        json={"title": "Tech Daily", "description": "All about technology."},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Authorization header missing."


def test_user_can_create_and_list_newspapers(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "creator@example.org")

    create_response = auth_test_client.post(
        NEWSPAPERS_URL,
        json={"title": "Tech Daily", "description": "All about technology."},
        headers=auth_headers(tokens["access_token"]),
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["title"] == "Tech Daily"
    assert created["description"] == "All about technology."
    assert created["owner_id"] == 1

    list_response = auth_test_client.get(NEWSPAPERS_URL)
    assert list_response.status_code == 200
    newspapers = list_response.json()
    assert len(newspapers) == 1
    assert newspapers[0]["title"] == "Tech Daily"


def test_non_owner_cannot_update_newspaper(auth_test_client: TestClient) -> None:
    creator_tokens = register_user(auth_test_client, "owner@example.org")
    stranger_tokens = register_user(auth_test_client, "intruder@example.org")

    created = auth_test_client.post(
        NEWSPAPERS_URL,
        json={"title": "My Paper", "description": "Original description."},
        headers=auth_headers(creator_tokens["access_token"]),
    )
    newspaper_id = created.json()["id"]

    update_response = auth_test_client.patch(
        f"{NEWSPAPERS_URL}/{newspaper_id}",
        json={"title": "Hacked Title"},
        headers=auth_headers(stranger_tokens["access_token"]),
    )

    assert update_response.status_code == 403
    assert update_response.json()["detail"] == "You do not have permission to modify this newspaper."


def test_owner_can_update_and_delete_newspaper(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "editor@example.org")

    created = auth_test_client.post(
        NEWSPAPERS_URL,
        json={"title": "Morning Post", "description": "Daily briefing."},
        headers=auth_headers(tokens["access_token"]),
    )
    newspaper_id = created.json()["id"]

    update_response = auth_test_client.patch(
        f"{NEWSPAPERS_URL}/{newspaper_id}",
        json={"title": "Evening Post", "description": "Updated."},
        headers=auth_headers(tokens["access_token"]),
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["title"] == "Evening Post"
    assert updated["description"] == "Updated."

    delete_response = auth_test_client.delete(
        f"{NEWSPAPERS_URL}/{newspaper_id}",
        headers=auth_headers(tokens["access_token"]),
    )
    assert delete_response.status_code == 204

    get_response = auth_test_client.get(f"{NEWSPAPERS_URL}/{newspaper_id}")
    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "Newspaper not found."


def test_get_newspaper_returns_articles(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "reporter@example.org")

    created = auth_test_client.post(
        NEWSPAPERS_URL,
        json={"title": "Science Weekly", "description": "Research highlights."},
        headers=auth_headers(tokens["access_token"]),
    )
    newspaper_id = created.json()["id"]

    article_response = auth_test_client.post(
        f"{NEWSPAPERS_URL}/{newspaper_id}/articles",
        json={
            "title": "New Discovery",
            "content": "Scientists announced a new discovery.",
            "url": "https://example.org/articles/discovery",
        },
        headers=auth_headers(tokens["access_token"]),
    )
    assert article_response.status_code == 201

    detail_response = auth_test_client.get(f"{NEWSPAPERS_URL}/{newspaper_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["title"] == "Science Weekly"
    assert len(detail["articles"]) == 1
    assert detail["articles"][0]["title"] == "New Discovery"
    assert detail["articles"][0]["newspaper_ids"] == [newspaper_id]

    filtered = auth_test_client.get(f"{NEWSPAPERS_URL}/{newspaper_id}/articles", params={"q": "Discovery"})
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1


def test_owner_can_share_and_unshare_newspaper(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "sharer@example.org")
    created = auth_test_client.post(
        NEWSPAPERS_URL,
        json={"title": "Sharing Paper", "description": "To be shared."},
        headers=auth_headers(tokens["access_token"]),
    ).json()
    newspaper_id = created["id"]
    assert created["is_public"] is False

    share_response = auth_test_client.post(
        f"{NEWSPAPERS_URL}/{newspaper_id}/share",
        json={"public": True},
        headers=auth_headers(tokens["access_token"]),
    )
    assert share_response.status_code == 200
    shared = share_response.json()
    assert shared["is_public"] is True
    assert shared["public_token"]
    assert shared["public_url"]

    public_fetch = auth_test_client.get(f"{PUBLIC_URL}/{shared['public_token']}")
    assert public_fetch.status_code == 200
    public_data = public_fetch.json()
    assert public_data["id"] == newspaper_id
    assert public_data["is_public"] is True

    unshare_response = auth_test_client.post(
        f"{NEWSPAPERS_URL}/{newspaper_id}/share",
        json={"public": False},
        headers=auth_headers(tokens["access_token"]),
    )
    assert unshare_response.status_code == 200
    unshared = unshare_response.json()
    assert unshared["is_public"] is False


def test_search_newspapers_supports_query_and_owner_filter(auth_test_client: TestClient) -> None:
    owner_tokens = register_user(auth_test_client, "publisher@example.org")
    other_tokens = register_user(auth_test_client, "another@example.org")

    auth_test_client.post(
        NEWSPAPERS_URL,
        json={"title": "Tech Daily", "description": "Tech news"},
        headers=auth_headers(owner_tokens["access_token"]),
    )
    auth_test_client.post(
        NEWSPAPERS_URL,
        json={"title": "Cooking Weekly", "description": "Recipes"},
        headers=auth_headers(owner_tokens["access_token"]),
    )
    auth_test_client.post(
        NEWSPAPERS_URL,
        json={"title": "Travel Digest", "description": "Trips"},
        headers=auth_headers(other_tokens["access_token"]),
    )

    search_response = auth_test_client.get(NEWSPAPERS_URL, params={"q": "Tech"})
    assert search_response.status_code == 200
    titles = [paper["title"] for paper in search_response.json()]
    assert titles == ["Tech Daily"]

    owner_response = auth_test_client.get(NEWSPAPERS_URL, params={"owner_email": "publisher@example.org"})
    assert owner_response.status_code == 200
    owner_titles = {paper["title"] for paper in owner_response.json()}
    assert owner_titles == {"Tech Daily", "Cooking Weekly"}
