"""Unit tests for AuthRepository with mocked database connections."""

from __future__ import annotations

from app.api.routes.auth.repository import AuthRepository


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

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass

    def close(self) -> None:
        pass


def create_mock_connection_factory(cursor: MockCursor):
    """Create a connection factory that returns a mock connection."""

    def factory():
        return MockConnection(cursor)

    return factory


class TestUserPreferencesRepositoryMixin:
    """Test the UserPreferencesRepositoryMixin methods."""

    def test_get_preferences_creates_row_if_not_exists(self):
        # First call ensures preferences row exists (fetchone returns None initially)
        # Then fetches the preferences
        cursor = MockCursor(rows=[("light", [])])
        factory = create_mock_connection_factory(cursor)
        repo = AuthRepository(connection_factory=factory)

        result = repo.get_preferences(user_id=1)

        assert result["theme"] == "light"
        assert result["hidden_source_ids"] == []

    def test_get_preferences_returns_existing_theme(self):
        cursor = MockCursor(rows=[("dark", [1, 2, 3])])
        factory = create_mock_connection_factory(cursor)
        repo = AuthRepository(connection_factory=factory)

        result = repo.get_preferences(user_id=1)

        assert result["theme"] == "dark"
        assert result["hidden_source_ids"] == [1, 2, 3]

    def test_get_preferences_returns_default_when_row_is_none(self):
        # First query (INSERT) doesn't return, second query (SELECT) returns None
        cursor = MockCursor(rows=[])
        factory = create_mock_connection_factory(cursor)
        repo = AuthRepository(connection_factory=factory)

        result = repo.get_preferences(user_id=1)

        assert result["theme"] == "light"
        assert result["hidden_source_ids"] == []

    def test_update_preferences_with_theme(self):
        # Returns updated preferences after update
        cursor = MockCursor(rows=[("dark", [])])
        factory = create_mock_connection_factory(cursor)
        repo = AuthRepository(connection_factory=factory)

        result = repo.update_preferences(user_id=1, theme="dark")

        assert result["theme"] == "dark"

    def test_update_preferences_with_hidden_source_ids(self):
        cursor = MockCursor(rows=[("light", [1, 2])])
        factory = create_mock_connection_factory(cursor)
        repo = AuthRepository(connection_factory=factory)

        result = repo.update_preferences(user_id=1, hidden_source_ids=[1, 2])

        assert result["hidden_source_ids"] == [1, 2]

    def test_update_preferences_with_both_fields(self):
        cursor = MockCursor(rows=[("dark", [5, 6])])
        factory = create_mock_connection_factory(cursor)
        repo = AuthRepository(connection_factory=factory)

        result = repo.update_preferences(user_id=1, theme="dark", hidden_source_ids=[5, 6])

        assert result["theme"] == "dark"
        assert result["hidden_source_ids"] == [5, 6]

    def test_update_preferences_with_no_changes(self):
        cursor = MockCursor(rows=[("light", [])])
        factory = create_mock_connection_factory(cursor)
        repo = AuthRepository(connection_factory=factory)

        result = repo.update_preferences(user_id=1)

        assert result["theme"] == "light"

    def test_add_hidden_source(self):
        cursor = MockCursor(rows=[("light", [1, 5])])
        factory = create_mock_connection_factory(cursor)
        repo = AuthRepository(connection_factory=factory)

        result = repo.add_hidden_source(user_id=1, source_id=5)

        assert 5 in result["hidden_source_ids"]

    def test_remove_hidden_source(self):
        cursor = MockCursor(rows=[("light", [1])])
        factory = create_mock_connection_factory(cursor)
        repo = AuthRepository(connection_factory=factory)

        result = repo.remove_hidden_source(user_id=1, source_id=5)

        assert 5 not in result["hidden_source_ids"]


class TestAuthRepositoryUserOperations:
    """Test user-related AuthRepository methods."""

    def test_email_exists_returns_true(self):
        cursor = MockCursor(rows=[(1,)])
        factory = create_mock_connection_factory(cursor)
        repo = AuthRepository(connection_factory=factory)

        result = repo.email_exists("test@example.com")

        assert result is True

    def test_email_exists_returns_false(self):
        cursor = MockCursor(rows=[])
        factory = create_mock_connection_factory(cursor)
        repo = AuthRepository(connection_factory=factory)

        result = repo.email_exists("nonexistent@example.com")

        assert result is False

    def test_create_user_returns_id(self):
        cursor = MockCursor(rows=[(42,)])
        factory = create_mock_connection_factory(cursor)
        repo = AuthRepository(connection_factory=factory)

        result = repo.create_user(email="new@example.com", password_hash="hashed_password")

        assert result == 42

    def test_get_user_credentials_returns_tuple(self):
        cursor = MockCursor(rows=[(1, "hashed_password")])
        factory = create_mock_connection_factory(cursor)
        repo = AuthRepository(connection_factory=factory)

        result = repo.get_user_credentials("test@example.com")

        assert result == (1, "hashed_password")

    def test_get_user_credentials_returns_none_when_not_found(self):
        cursor = MockCursor(rows=[])
        factory = create_mock_connection_factory(cursor)
        repo = AuthRepository(connection_factory=factory)

        result = repo.get_user_credentials("nonexistent@example.com")

        assert result is None

    def test_get_user_id_returns_id(self):
        cursor = MockCursor(rows=[(42,)])
        factory = create_mock_connection_factory(cursor)
        repo = AuthRepository(connection_factory=factory)

        result = repo.get_user_id("test@example.com")

        assert result == 42

    def test_get_user_id_returns_none_when_not_found(self):
        cursor = MockCursor(rows=[])
        factory = create_mock_connection_factory(cursor)
        repo = AuthRepository(connection_factory=factory)

        result = repo.get_user_id("nonexistent@example.com")

        assert result is None

    def test_delete_user_success(self):
        cursor = MockCursor(rowcount=1)
        factory = create_mock_connection_factory(cursor)
        repo = AuthRepository(connection_factory=factory)

        result = repo.delete_user(user_id=1)

        assert result is True

    def test_delete_user_not_found(self):
        cursor = MockCursor(rowcount=0)
        factory = create_mock_connection_factory(cursor)
        repo = AuthRepository(connection_factory=factory)

        result = repo.delete_user(user_id=999)

        assert result is False


class TestAuthRepositoryTokenOperations:
    """Test token-related AuthRepository methods."""

    def test_store_tokens(self):
        cursor = MockCursor()
        factory = create_mock_connection_factory(cursor)
        repo = AuthRepository(connection_factory=factory)

        # Should not raise
        repo.store_tokens(user_id=1, access_token="access123", refresh_token="refresh456")

        # Verify queries were executed
        assert len(cursor.executed_queries) == 2  # DELETE and INSERT

    def test_get_email_by_access_token_returns_email(self):
        cursor = MockCursor(rows=[("user@example.com",)])
        factory = create_mock_connection_factory(cursor)
        repo = AuthRepository(connection_factory=factory)

        result = repo.get_email_by_access_token("valid_access_token")

        assert result == "user@example.com"

    def test_get_email_by_access_token_returns_none_when_not_found(self):
        cursor = MockCursor(rows=[])
        factory = create_mock_connection_factory(cursor)
        repo = AuthRepository(connection_factory=factory)

        result = repo.get_email_by_access_token("invalid_token")

        assert result is None

    def test_get_user_id_by_refresh_token_returns_id(self):
        cursor = MockCursor(rows=[(42,)])
        factory = create_mock_connection_factory(cursor)
        repo = AuthRepository(connection_factory=factory)

        result = repo.get_user_id_by_refresh_token("valid_refresh_token")

        assert result == 42

    def test_get_user_id_by_refresh_token_returns_none_when_not_found(self):
        cursor = MockCursor(rows=[])
        factory = create_mock_connection_factory(cursor)
        repo = AuthRepository(connection_factory=factory)

        result = repo.get_user_id_by_refresh_token("invalid_token")

        assert result is None

    def test_delete_tokens_for_user(self):
        cursor = MockCursor()
        factory = create_mock_connection_factory(cursor)
        repo = AuthRepository(connection_factory=factory)

        # Should not raise
        repo.delete_tokens_for_user(user_id=1)

        # Verify DELETE query was executed
        assert len(cursor.executed_queries) == 1


class TestAuthRepositoryIntegration:
    """Integration-style tests for AuthRepository."""

    def test_full_user_lifecycle(self):
        # Simulate creating user, storing tokens, getting credentials, and deleting
        cursor = MockCursor(
            rows=[
                (1,),  # create_user returns id
                (1, "hashed_password"),  # get_user_credentials
                ("user@example.com",),  # get_email_by_access_token
            ]
        )
        cursor.rowcount = 1  # For delete_user
        factory = create_mock_connection_factory(cursor)
        repo = AuthRepository(connection_factory=factory)

        # Create user
        user_id = repo.create_user("user@example.com", "hashed_password")
        assert user_id == 1

        # Get credentials
        credentials = repo.get_user_credentials("user@example.com")
        assert credentials == (1, "hashed_password")

        # Store tokens
        repo.store_tokens(user_id, "access_token", "refresh_token")

        # Get email by access token
        email = repo.get_email_by_access_token("access_token")
        assert email == "user@example.com"
