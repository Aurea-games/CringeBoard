from typing import Callable, Optional, Tuple

from app.core.db import get_connection


class AuthRepository:
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

    def get_user_credentials(self, email: str) -> Optional[Tuple[int, str]]:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute("SELECT id, password_hash FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
            if not row:
                return None
            return row[0], row[1]

    def get_user_id(self, email: str) -> Optional[int]:
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

    def get_email_by_access_token(self, token: str) -> Optional[str]:
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

    def delete_tokens_for_user(self, user_id: int) -> None:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM tokens WHERE user_id = %s", (user_id,))


__all__ = ["AuthRepository"]
