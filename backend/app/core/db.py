from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

import psycopg


def _normalize_dsn(raw_dsn: str) -> str:
    """Translate SQLAlchemy-style URLs into psycopg-compatible DSNs."""
    if raw_dsn.startswith("postgresql+"):
        scheme, rest = raw_dsn.split("+", 1)
        if "://" in rest:
            _, remainder = rest.split("://", 1)
            return f"{scheme}://{remainder}"
    return raw_dsn


def _load_dsn() -> str:
    raw_dsn = os.getenv("DATABASE_URL")
    if not raw_dsn:
        raise RuntimeError("DATABASE_URL environment variable is required.")
    return _normalize_dsn(raw_dsn)


DATABASE_DSN = _load_dsn()


def ensure_schema() -> None:
    """Create required tables if they do not already exist."""
    with psycopg.connect(DATABASE_DSN, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS tokens (
                    token TEXT PRIMARY KEY,
                    token_type TEXT NOT NULL,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS ix_tokens_user_id ON tokens (user_id);
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS newspapers (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS ix_newspapers_owner_id ON newspapers (owner_id);
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS articles (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT,
                    url TEXT,
                    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS ix_articles_owner_id ON articles (owner_id);
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS article_favorites (
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (user_id, article_id)
                );
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS ix_article_favorites_article_id ON article_favorites (article_id);
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS article_read_later (
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (user_id, article_id)
                );
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS ix_article_read_later_article_id ON article_read_later (article_id);
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS ix_article_read_later_user_id ON article_read_later (user_id);
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS newspaper_articles (
                    newspaper_id INTEGER NOT NULL REFERENCES newspapers(id) ON DELETE CASCADE,
                    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (newspaper_id, article_id)
                );
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS ix_newspaper_articles_article_id ON newspaper_articles (article_id);
                """
            )


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    """Yield a psycopg connection with automatic commit/rollback."""
    conn = psycopg.connect(DATABASE_DSN)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


ensure_schema()

__all__ = ["get_connection", "ensure_schema", "DATABASE_DSN"]
