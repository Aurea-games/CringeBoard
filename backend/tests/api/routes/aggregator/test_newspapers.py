from __future__ import annotations

from fastapi.testclient import TestClient

NEWSPAPERS_URL = "/v1/newspapers"


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
