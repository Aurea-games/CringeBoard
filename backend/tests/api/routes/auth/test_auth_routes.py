from fastapi.testclient import TestClient

REGISTER_URL = "/v1/auth/register"
LOGIN_URL = "/v1/auth/login"
REFRESH_URL = "/v1/auth/refresh"
DELETE_URL = "/v1/auth/users/me"
PREFERENCES_URL = "/v1/auth/users/me/preferences"
PREFERENCES_HIDE_URL = "/v1/auth/users/me/preferences/hide-source"


def register_user(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post(
        REGISTER_URL,
        json={
            "email": email,
            "password": password,
            "confirm_password": password,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_register_returns_tokens(auth_test_client: TestClient) -> None:
    response = auth_test_client.post(
        REGISTER_URL,
        json={
            "email": "user@example.org",
            "password": "StrongPass1",
            "confirm_password": "StrongPass1",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


def test_register_rejects_duplicate_email(auth_test_client: TestClient) -> None:
    payload = {
        "email": "dupe@example.org",
        "password": "StrongPass1",
        "confirm_password": "StrongPass1",
    }
    first = auth_test_client.post(REGISTER_URL, json=payload)
    assert first.status_code == 201

    second = auth_test_client.post(REGISTER_URL, json=payload)
    assert second.status_code == 400
    assert second.json()["detail"] == "This email is already registered."


def test_login_returns_tokens_for_valid_credentials(auth_test_client: TestClient) -> None:
    register_user(auth_test_client, "login@example.org", "StrongPass1")

    response = auth_test_client.post(
        LOGIN_URL,
        json={
            "email": "login@example.org",
            "password": "StrongPass1",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


def test_login_rejects_invalid_credentials(auth_test_client: TestClient) -> None:
    response = auth_test_client.post(
        LOGIN_URL,
        json={
            "email": "unknown@example.org",
            "password": "does-not-matter",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials."


def test_login_requires_non_empty_password(auth_test_client: TestClient) -> None:
    response = auth_test_client.post(
        LOGIN_URL,
        json={
            "email": "someone@example.org",
            "password": "",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Password must not be empty."


def test_refresh_issues_new_token_pair(auth_test_client: TestClient) -> None:
    initial_tokens = register_user(auth_test_client, "refresh@example.org", "StrongPass1")

    response = auth_test_client.post(
        REFRESH_URL,
        json={"refresh_token": initial_tokens["refresh_token"]},
    )

    assert response.status_code == 200
    refreshed = response.json()
    assert refreshed["access_token"] != initial_tokens["access_token"]
    assert refreshed["refresh_token"] != initial_tokens["refresh_token"]
    assert refreshed["token_type"] == "bearer"

    retry = auth_test_client.post(
        REFRESH_URL,
        json={"refresh_token": initial_tokens["refresh_token"]},
    )
    assert retry.status_code == 401
    assert retry.json()["detail"] == "Invalid or expired refresh token."


def test_refresh_rejects_unknown_token(auth_test_client: TestClient) -> None:
    response = auth_test_client.post(
        REFRESH_URL,
        json={"refresh_token": "not-a-real-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired refresh token."


def test_delete_me_removes_account_and_tokens(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "remove@example.org", "StrongPass1")

    delete_response = auth_test_client.delete(
        DELETE_URL,
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert delete_response.status_code == 204

    login_after_delete = auth_test_client.post(
        LOGIN_URL,
        json={
            "email": "remove@example.org",
            "password": "StrongPass1",
        },
    )
    assert login_after_delete.status_code == 401
    assert login_after_delete.json()["detail"] == "Invalid credentials."

    re_register = auth_test_client.post(
        REGISTER_URL,
        json={
            "email": "remove@example.org",
            "password": "StrongPass1",
            "confirm_password": "StrongPass1",
        },
    )
    assert re_register.status_code == 201


def test_delete_requires_valid_authorization(auth_test_client: TestClient) -> None:
    response = auth_test_client.delete(DELETE_URL)

    assert response.status_code == 401
    assert response.json()["detail"] == "Authorization header missing."


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_preferences_default_and_update(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "prefs@example.org", "StrongPass1")

    default_response = auth_test_client.get(PREFERENCES_URL, headers=auth_headers(tokens["access_token"]))
    assert default_response.status_code == 200
    assert default_response.json() == {"theme": "light", "hidden_source_ids": []}

    update_response = auth_test_client.put(
        PREFERENCES_URL,
        json={"theme": "dark", "hidden_source_ids": [1, 2]},
        headers=auth_headers(tokens["access_token"]),
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["theme"] == "dark"
    assert updated["hidden_source_ids"] == [1, 2]


def test_preferences_hide_and_unhide_sources(auth_test_client: TestClient) -> None:
    tokens = register_user(auth_test_client, "prefs2@example.org", "StrongPass1")
    headers = auth_headers(tokens["access_token"])

    hide_response = auth_test_client.post(
        PREFERENCES_HIDE_URL,
        json={"sourceId": 5},
        headers=headers,
    )
    assert hide_response.status_code == 200
    assert hide_response.json()["hidden_source_ids"] == [5]

    hide_second = auth_test_client.post(
        PREFERENCES_HIDE_URL,
        json={"sourceId": 7},
        headers=headers,
    )
    assert hide_second.status_code == 200
    assert hide_second.json()["hidden_source_ids"] == [5, 7]

    unhide_response = auth_test_client.delete(f"{PREFERENCES_HIDE_URL}/5", headers=headers)
    assert unhide_response.status_code == 200
    assert unhide_response.json()["hidden_source_ids"] == [7]
