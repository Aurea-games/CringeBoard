from __future__ import annotations

from fastapi.testclient import TestClient

NEWSPAPERS_URL = "/v1/newspapers"
SOURCES_URL = "/v1/sources"
NOTIFICATIONS_URL = "/v1/me/notifications"


def register_user(client: TestClient, email: str) -> dict[str, str]:
    response = client.post(
        "/v1/auth/register",
        json={"email": email, "password": "StrongPass1", "confirm_password": "StrongPass1"},
    )
    assert response.status_code == 201
    return response.json()


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_notifications_for_followed_source(auth_test_client: TestClient) -> None:
    follower = register_user(auth_test_client, "notify-follower@example.org")
    owner = register_user(auth_test_client, "notify-owner@example.org")

    source = auth_test_client.post(
        SOURCES_URL,
        json={"name": "Notif Source"},
        headers=auth_headers(owner["access_token"]),
    ).json()

    follow_response = auth_test_client.post(
        f"{SOURCES_URL}/{source['id']}/follow",
        headers=auth_headers(follower["access_token"]),
    )
    assert follow_response.status_code == 200

    newspaper_response = auth_test_client.post(
        NEWSPAPERS_URL,
        json={"title": "Source Daily", "description": "News drop", "source_id": source["id"]},
        headers=auth_headers(owner["access_token"]),
    )
    assert newspaper_response.status_code == 201
    newspaper = newspaper_response.json()

    unread_response = auth_test_client.get(NOTIFICATIONS_URL, headers=auth_headers(follower["access_token"]))
    assert unread_response.status_code == 200
    unread = unread_response.json()
    assert len(unread) == 1
    first = unread[0]
    assert first["source_id"] == source["id"]
    assert first["newspaper_id"] == newspaper["id"]
    assert first["article_id"] is None
    assert first["is_read"] is False
    assert "Source Daily" in first["message"]

    mark_response = auth_test_client.post(
        f"{NOTIFICATIONS_URL}/{first['id']}/read",
        headers=auth_headers(follower["access_token"]),
    )
    assert mark_response.status_code == 200
    assert mark_response.json()["is_read"] is True

    after_mark = auth_test_client.get(NOTIFICATIONS_URL, headers=auth_headers(follower["access_token"]))
    assert after_mark.status_code == 200
    assert after_mark.json() == []

    include_read = auth_test_client.get(
        NOTIFICATIONS_URL,
        params={"include_read": True},
        headers=auth_headers(follower["access_token"]),
    )
    assert include_read.status_code == 200
    assert len(include_read.json()) == 1

    article_response = auth_test_client.post(
        f"{NEWSPAPERS_URL}/{newspaper['id']}/articles",
        json={"title": "Fresh Article", "content": None, "url": None},
        headers=auth_headers(owner["access_token"]),
    )
    assert article_response.status_code == 201
    article = article_response.json()

    after_article = auth_test_client.get(NOTIFICATIONS_URL, headers=auth_headers(follower["access_token"]))
    assert after_article.status_code == 200
    notifications = after_article.json()
    assert len(notifications) == 1
    latest = notifications[0]
    assert latest["article_id"] == article["id"]
    assert latest["newspaper_id"] == newspaper["id"]
    assert latest["is_read"] is False
    assert "Fresh Article" in latest["message"]
