from collections.abc import Callable

from app.core.db import get_connection


class UserPreferencesRepositoryMixin:
    """Preference related data access shared with AuthRepository."""

    _DEFAULT_THEME = "light"

    def _ensure_preferences_row(self, cur, user_id: int) -> None:
        cur.execute(
            """
            INSERT INTO user_preferences (user_id, theme, hidden_source_ids)
            VALUES (%s, %s, ARRAY[]::INTEGER[])
            ON CONFLICT (user_id) DO NOTHING
            """,
            (user_id, self._DEFAULT_THEME),
        )

    def get_preferences(self, user_id: int) -> dict[str, object]:
        with self._connection_factory() as conn, conn.cursor() as cur:
            self._ensure_preferences_row(cur, user_id)
            cur.execute(
                """
                SELECT theme, COALESCE(hidden_source_ids, ARRAY[]::INTEGER[])
                FROM user_preferences
                WHERE user_id = %s
                """,
                (user_id,),
            )
            row = cur.fetchone()
            if row is None:
                return {"theme": self._DEFAULT_THEME, "hidden_source_ids": []}
            theme, hidden_source_ids = row
            return {
                "theme": theme,
                "hidden_source_ids": [int(identifier) for identifier in hidden_source_ids],
            }

    def update_preferences(
        self,
        user_id: int,
        theme: str | None = None,
        hidden_source_ids: list[int] | None = None,
    ) -> dict[str, object]:
        assignments: list[str] = []
        params: list[object] = []
        with self._connection_factory() as conn, conn.cursor() as cur:
            self._ensure_preferences_row(cur, user_id)
            if theme is not None:
                assignments.append("theme = %s")
                params.append(theme)
            if hidden_source_ids is not None:
                assignments.append("hidden_source_ids = %s")
                params.append(hidden_source_ids)
            if assignments:
                params.append(user_id)
                cur.execute(
                    f"""
                    UPDATE user_preferences
                    SET {", ".join(assignments)}, updated_at = NOW()
                    WHERE user_id = %s
                    """,
                    tuple(params),
                )
            return self.get_preferences(user_id)

    def add_hidden_source(self, user_id: int, source_id: int) -> dict[str, object]:
        with self._connection_factory() as conn, conn.cursor() as cur:
            self._ensure_preferences_row(cur, user_id)
            cur.execute(
                """
                UPDATE user_preferences
                SET hidden_source_ids = (
                    SELECT ARRAY(
                        SELECT DISTINCT identifier
                        FROM UNNEST(hidden_source_ids || %s::INTEGER) AS t(identifier)
                    )
                ),
                updated_at = NOW()
                WHERE user_id = %s
                """,
                ([source_id], user_id),
            )
            return self.get_preferences(user_id)

    def remove_hidden_source(self, user_id: int, source_id: int) -> dict[str, object]:
        with self._connection_factory() as conn, conn.cursor() as cur:
            self._ensure_preferences_row(cur, user_id)
            cur.execute(
                """
                UPDATE user_preferences
                SET hidden_source_ids = ARRAY(
                    SELECT identifier
                    FROM UNNEST(hidden_source_ids) AS t(identifier)
                    WHERE identifier <> %s
                ),
                updated_at = NOW()
                WHERE user_id = %s
                """,
                (source_id, user_id),
            )
            return self.get_preferences(user_id)


class AuthRepository(UserPreferencesRepositoryMixin):
    """Data access layer for persisting and retrieving authentication data."""

    def __init__(self, connection_factory: Callable = get_connection) -> None:
        self._connection_factory = connection_factory

    def email_exists(self, email: str) -> bool:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE email = %s", (email,))
            return cur.fetchone() is not None

    def create_user(self, email: str, password_hash: str) -> int:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (email, password_hash)
                VALUES (%s, %s)
                RETURNING id
                """,
                (email, password_hash),
            )
            row = cur.fetchone()
            return row[0]

    def get_user_credentials(self, email: str) -> tuple[int, str] | None:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute("SELECT id, password_hash FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
            if not row:
                return None
            return row[0], row[1]

    def get_user_id(self, email: str) -> int | None:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
            return row[0] if row else None

    def delete_user(self, user_id: int) -> bool:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
            return cur.rowcount > 0

    def store_tokens(self, user_id: int, access_token: str, refresh_token: str) -> None:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM tokens WHERE user_id = %s", (user_id,))
            cur.execute(
                """
                INSERT INTO tokens (token, token_type, user_id)
                VALUES (%s, 'access', %s), (%s, 'refresh', %s)
                """,
                (access_token, user_id, refresh_token, user_id),
            )

    def get_email_by_access_token(self, token: str) -> str | None:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT u.email
                FROM tokens AS t
                JOIN users AS u ON u.id = t.user_id
                WHERE t.token = %s AND t.token_type = 'access'
                """,
                (token,),
            )
            row = cur.fetchone()
            return row[0] if row else None

    def get_user_id_by_refresh_token(self, token: str) -> int | None:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT t.user_id
                FROM tokens AS t
                WHERE t.token = %s AND t.token_type = 'refresh'
                """,
                (token,),
            )
            row = cur.fetchone()
            return row[0] if row else None

    def delete_tokens_for_user(self, user_id: int) -> None:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM tokens WHERE user_id = %s", (user_id,))


__all__ = ["AuthRepository"]
