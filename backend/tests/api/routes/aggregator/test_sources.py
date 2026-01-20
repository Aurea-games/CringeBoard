from __future__ import annotations

from fastapi.testclient import TestClient

SOURCES_URL = "/v1/sources"
ME_SOURCES_URL = "/v1/me/sources"


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


def test_create_source_requires_auth(auth_test_client: TestClient) -> None:
    response = auth_test_client.post(SOURCES_URL, json={"name": "TechCrunch"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Authorization header missing."


def test_create_list_and_update_source(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "sources@example.org")
    create_response = auth_test_client.post(
        SOURCES_URL,
        json={"name": "TechCrunch", "feed_url": "https://techcrunch.com/feed/"},
        headers=auth_headers(tokens["access_token"]),
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == "TechCrunch"
    assert created["feed_url"] == "https://techcrunch.com/feed/"
    assert created["is_followed"] is False

    list_response = auth_test_client.get(SOURCES_URL)
    assert list_response.status_code == 200
    listed = list_response.json()
    assert len(listed) == 1
    assert listed[0]["name"] == "TechCrunch"

    patch_response = auth_test_client.patch(
        f"{SOURCES_URL}/{created['id']}",
        json={"description": "Tech news"},
        headers=auth_headers(tokens["access_token"]),
    )
    assert patch_response.status_code == 200
    updated = patch_response.json()
    assert updated["description"] == "Tech news"


def test_follow_and_unfollow_source(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "follower@example.org")
    creator_tokens = register_user(auth_test_client, "creator@example.org")

    source = auth_test_client.post(
        SOURCES_URL,
        json={"name": "Hacker News", "feed_url": "https://hnrss.org/frontpage"},
        headers=auth_headers(creator_tokens["access_token"]),
    ).json()

    follow_response = auth_test_client.post(
        f"{SOURCES_URL}/{source['id']}/follow",
        headers=auth_headers(tokens["access_token"]),
    )
    assert follow_response.status_code == 200
    followed = follow_response.json()
    assert followed["is_followed"] is True

    # Listing with auth should reflect follow flag
    list_response = auth_test_client.get(
        SOURCES_URL,
        headers=auth_headers(tokens["access_token"]),
    )
    assert list_response.status_code == 200
    assert list_response.json()[0]["is_followed"] is True

    me_list = auth_test_client.get(ME_SOURCES_URL, headers=auth_headers(tokens["access_token"]))
    assert me_list.status_code == 200
    assert len(me_list.json()) == 1
    assert me_list.json()[0]["id"] == source["id"]

    unfollow_response = auth_test_client.delete(
        f"{SOURCES_URL}/{source['id']}/follow",
        headers=auth_headers(tokens["access_token"]),
    )
    assert unfollow_response.status_code == 204

    me_after = auth_test_client.get(ME_SOURCES_URL, headers=auth_headers(tokens["access_token"]))
    assert me_after.status_code == 200
    assert me_after.json() == []

    single = auth_test_client.get(
        f"{SOURCES_URL}/{source['id']}",
        headers=auth_headers(tokens["access_token"]),
    )
    assert single.status_code == 200
    assert single.json()["is_followed"] is False
