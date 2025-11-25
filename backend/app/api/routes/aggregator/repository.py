from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.core.db import get_connection

NewspaperRow = dict[str, Any]
ArticleRow = dict[str, Any]


class AggregatorRepository:
    """CRUD operations for newspapers and articles."""

    def __init__(self, connection_factory: Callable = get_connection) -> None:
        self._connection_factory = connection_factory

    @staticmethod
    def row_to_newspaper(row: tuple[Any, ...] | None) -> NewspaperRow | None:
        if row is None:
            return None
        return {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "owner_id": row[3],
            "created_at": row[4],
            "updated_at": row[5],
        }

    @staticmethod
    def normalize_newspaper_ids(raw_ids: Any) -> list[int]:
        if raw_ids is None:
            return []
        return [int(identifier) for identifier in raw_ids]

    @classmethod
    def row_to_article(cls, row: tuple[Any, ...] | None) -> ArticleRow | None:
        if row is None:
            return None
        return {
            "id": row[0],
            "title": row[1],
            "content": row[2],
            "url": row[3],
            "owner_id": row[4],
            "created_at": row[5],
            "updated_at": row[6],
            "newspaper_ids": cls.normalize_newspaper_ids(row[7]),
        }

    def create_newspaper(self, owner_id: int, title: str, description: str | None) -> NewspaperRow:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO newspapers (title, description, owner_id)
                VALUES (%s, %s, %s)
                RETURNING id, title, description, owner_id, created_at, updated_at
                """,
                (title, description, owner_id),
            )
            row = cur.fetchone()
        if row is None:
            raise RuntimeError("Failed to create newspaper.")
        newspaper = self.row_to_newspaper(row)
        if newspaper is None:
            raise RuntimeError("Failed to map created newspaper.")
        return newspaper

    def list_newspapers(self) -> list[NewspaperRow]:
        return self.search_newspapers()

    def search_newspapers(self, search: str | None = None, owner_id: int | None = None) -> list[NewspaperRow]:
        clauses: list[str] = []
        params: list[Any] = []

        if owner_id is not None:
            clauses.append("owner_id = %s")
            params.append(owner_id)

        pattern: str | None = None
        if search:
            trimmed = search.strip()
            if trimmed:
                pattern = f"%{trimmed}%"
                clauses.append("(title ILIKE %s OR description ILIKE %s)")
                params.extend([pattern, pattern])

        sql = [
            "SELECT id, title, description, owner_id, created_at, updated_at",
            "FROM newspapers",
        ]
        if clauses:
            sql.append("WHERE " + " AND ".join(clauses))
        sql.append("ORDER BY created_at DESC")

        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute("\n".join(sql), tuple(params))
            rows = cur.fetchall()

        result: list[NewspaperRow] = []
        for row in rows:
            newspaper = self.row_to_newspaper(row)
            if newspaper is not None:
                result.append(newspaper)
        return result

    def find_newspaper_by_title(self, owner_id: int, title: str) -> NewspaperRow | None:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, description, owner_id, created_at, updated_at
                FROM newspapers
                WHERE owner_id = %s AND title = %s
                """,
                (owner_id, title),
            )
            row = cur.fetchone()
        return self.row_to_newspaper(row)

    def get_newspaper(self, newspaper_id: int) -> NewspaperRow | None:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, description, owner_id, created_at, updated_at
                FROM newspapers
                WHERE id = %s
                """,
                (newspaper_id,),
            )
            row = cur.fetchone()
        return self.row_to_newspaper(row)

    def update_newspaper(
        self,
        newspaper_id: int,
        title: str | None,
        description: str | None,
    ) -> NewspaperRow | None:
        assignments: list[str] = []
        params: list[Any] = []

        if title is not None:
            assignments.append("title = %s")
            params.append(title)
        if description is not None:
            assignments.append("description = %s")
            params.append(description)

        set_clause = ", ".join(assignments)
        if set_clause:
            set_clause = f"{set_clause}, "

        params.append(newspaper_id)

        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE newspapers
                SET {set_clause}updated_at = NOW()
                WHERE id = %s
                RETURNING id, title, description, owner_id, created_at, updated_at
                """,
                tuple(params),
            )
            row = cur.fetchone()
        return self.row_to_newspaper(row)

    def delete_newspaper(self, newspaper_id: int) -> bool:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM newspapers WHERE id = %s", (newspaper_id,))
            return cur.rowcount > 0

    def list_articles_for_newspaper(self, newspaper_id: int) -> list[ArticleRow]:
        return self.search_articles(newspaper_id=newspaper_id)

    def search_articles(
        self,
        search: str | None = None,
        owner_id: int | None = None,
        newspaper_id: int | None = None,
    ) -> list[ArticleRow]:
        clauses: list[str] = []
        params: list[Any] = []

        if newspaper_id is not None:
            clauses.append(
                """
                EXISTS (
                    SELECT 1
                    FROM newspaper_articles AS na
                    WHERE na.article_id = a.id AND na.newspaper_id = %s
                )
                """.strip()
            )
            params.append(newspaper_id)

        if owner_id is not None:
            clauses.append("a.owner_id = %s")
            params.append(owner_id)

        if search:
            trimmed = search.strip()
            if trimmed:
                pattern = f"%{trimmed}%"
                clauses.append("(a.title ILIKE %s OR a.content ILIKE %s)")
                params.extend([pattern, pattern])

        sql = [
            """
            SELECT
                a.id,
                a.title,
                a.content,
                a.url,
                a.owner_id,
                a.created_at,
                a.updated_at,
                COALESCE(
                    ARRAY(
                        SELECT na2.newspaper_id
                        FROM newspaper_articles AS na2
                        WHERE na2.article_id = a.id
                        ORDER BY na2.newspaper_id
                    ),
                    ARRAY[]::INTEGER[]
                ) AS newspaper_ids
            FROM articles AS a
            """
        ]
        if clauses:
            sql.append("WHERE " + " AND ".join(clauses))
        sql.append("ORDER BY a.created_at DESC")

        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute("\n".join(sql), tuple(params))
            rows = cur.fetchall()

        result: list[ArticleRow] = []
        for row in rows:
            article = self.row_to_article(row)
            if article is not None:
                result.append(article)
        return result

    def fetch_article(self, cursor, article_id: int) -> ArticleRow | None:
        cursor.execute(
            """
            SELECT
                a.id,
                a.title,
                a.content,
                a.url,
                a.owner_id,
                a.created_at,
                a.updated_at,
                COALESCE(
                    ARRAY(
                        SELECT na.newspaper_id
                        FROM newspaper_articles AS na
                        WHERE na.article_id = a.id
                        ORDER BY na.newspaper_id
                    ),
                    ARRAY[]::INTEGER[]
                ) AS newspaper_ids
            FROM articles AS a
            WHERE a.id = %s
            """,
            (article_id,),
        )
        row = cursor.fetchone()
        return self.row_to_article(row)

    def create_article(
        self,
        owner_id: int,
        newspaper_id: int,
        title: str,
        content: str | None,
        url: str | None,
    ) -> ArticleRow:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO articles (title, content, url, owner_id)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (title, content, url, owner_id),
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("Failed to create article.")
            article_id = row[0]
            cur.execute(
                """
                INSERT INTO newspaper_articles (newspaper_id, article_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (newspaper_id, article_id),
            )
            article = self.fetch_article(cur, article_id)
        if article is None:
            raise RuntimeError("Failed to map created article.")
        return article

    def get_article(self, article_id: int) -> ArticleRow | None:
        with self._connection_factory() as conn, conn.cursor() as cur:
            return self.fetch_article(cur, article_id)

    def find_article_by_url(self, url: str) -> ArticleRow | None:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    a.id,
                    a.title,
                    a.content,
                    a.url,
                    a.owner_id,
                    a.created_at,
                    a.updated_at,
                    COALESCE(
                        ARRAY(
                            SELECT na.newspaper_id
                            FROM newspaper_articles AS na
                            WHERE na.article_id = a.id
                            ORDER BY na.newspaper_id
                        ),
                        ARRAY[]::INTEGER[]
                    ) AS newspaper_ids
                FROM articles AS a
                WHERE a.url = %s
                LIMIT 1
                """,
                (url,),
            )
            row = cur.fetchone()
        return self.row_to_article(row)

    def update_article(
        self,
        article_id: int,
        title: str | None,
        content: str | None,
        url: str | None,
    ) -> ArticleRow | None:
        assignments: list[str] = []
        params: list[Any] = []

        if title is not None:
            assignments.append("title = %s")
            params.append(title)
        if content is not None:
            assignments.append("content = %s")
            params.append(content)
        if url is not None:
            assignments.append("url = %s")
            params.append(url)

        set_clause = ", ".join(assignments)
        if set_clause:
            set_clause = f"{set_clause}, "

        params.append(article_id)

        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE articles
                SET {set_clause}updated_at = NOW()
                WHERE id = %s
                RETURNING id
                """,
                tuple(params),
            )
            row = cur.fetchone()
            if row is None:
                return None
            article_id = row[0]
            return self.fetch_article(cur, article_id)

    def assign_article_to_newspaper(self, article_id: int, newspaper_id: int) -> ArticleRow | None:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO newspaper_articles (newspaper_id, article_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (newspaper_id, article_id),
            )
            return self.fetch_article(cur, article_id)

    def detach_article_from_newspaper(self, article_id: int, newspaper_id: int) -> ArticleRow | None:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM newspaper_articles
                WHERE newspaper_id = %s AND article_id = %s
                """,
                (newspaper_id, article_id),
            )
            # return updated article row (may still exist in other newspapers)
            return self.fetch_article(cur, article_id)

    def delete_article(self, article_id: int) -> bool:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM articles WHERE id = %s", (article_id,))
            return cur.rowcount > 0
