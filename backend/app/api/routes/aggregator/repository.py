from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.core.db import get_connection

NewspaperRow = dict[str, Any]
ArticleRow = dict[str, Any]
SourceRow = dict[str, Any]
NotificationRow = dict[str, Any]


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
            "is_public": row[4],
            "public_token": row[5],
            "created_at": row[6],
            "updated_at": row[7],
            "source_id": row[8],
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
            "popularity": row[5],
            "created_at": row[6],
            "updated_at": row[7],
            "newspaper_ids": cls.normalize_newspaper_ids(row[8]),
        }

    @staticmethod
    def row_to_source(row: tuple[Any, ...] | None) -> SourceRow | None:
        if row is None:
            return None
        # row may include is_followed appended by queries
        base_length = 7
        is_followed = False
        if len(row) > base_length:
            is_followed = bool(row[7])
        return {
            "id": row[0],
            "name": row[1],
            "feed_url": row[2],
            "description": row[3],
            "status": row[4],
            "created_at": row[5],
            "updated_at": row[6],
            "is_followed": is_followed,
        }

    @staticmethod
    def row_to_notification(row: tuple[Any, ...] | None) -> NotificationRow | None:
        if row is None:
            return None
        return {
            "id": row[0],
            "user_id": row[1],
            "source_id": row[2],
            "article_id": row[3],
            "newspaper_id": row[4],
            "message": row[5],
            "is_read": row[6],
            "created_at": row[7],
        }

    def create_newspaper(
        self,
        owner_id: int,
        title: str,
        description: str | None,
        source_id: int | None = None,
    ) -> NewspaperRow:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO newspapers (title, description, owner_id, source_id)
                VALUES (%s, %s, %s, %s)
                RETURNING id, title, description, owner_id, is_public, public_token, created_at, updated_at, source_id
                """,
                (title, description, owner_id, source_id),
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
            "SELECT id, title, description, owner_id, is_public, public_token, created_at, updated_at, source_id",
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
                SELECT id, title, description, owner_id, is_public, public_token, created_at, updated_at, source_id
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
                SELECT id, title, description, owner_id, is_public, public_token, created_at, updated_at, source_id
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
        source_id: int | None,
        update_source_id: bool = False,
    ) -> NewspaperRow | None:
        assignments: list[str] = []
        params: list[Any] = []

        if title is not None:
            assignments.append("title = %s")
            params.append(title)
        if description is not None:
            assignments.append("description = %s")
            params.append(description)
        if update_source_id:
            assignments.append("source_id = %s")
            params.append(source_id)

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
                RETURNING id, title, description, owner_id, is_public, public_token, created_at, updated_at, source_id
                """,
                tuple(params),
            )
            row = cur.fetchone()
        return self.row_to_newspaper(row)

    def delete_newspaper(self, newspaper_id: int) -> bool:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM newspapers WHERE id = %s", (newspaper_id,))
            return cur.rowcount > 0

    def update_newspaper_publication(
        self,
        newspaper_id: int,
        is_public: bool,
        public_token: str | None,
    ) -> NewspaperRow | None:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE newspapers
                SET is_public = %s,
                    public_token = %s,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING id, title, description, owner_id, is_public, public_token, created_at, updated_at, source_id
                """,
                (is_public, public_token, newspaper_id),
            )
            row = cur.fetchone()
        return self.row_to_newspaper(row)

    def get_newspaper_by_token(self, token: str) -> NewspaperRow | None:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, description, owner_id, is_public, public_token, created_at, updated_at, source_id
                FROM newspapers
                WHERE public_token = %s AND is_public = TRUE
                """,
                (token,),
            )
            row = cur.fetchone()
        return self.row_to_newspaper(row)

    def list_articles_for_newspaper(self, newspaper_id: int) -> list[ArticleRow]:
        return self.search_articles(newspaper_id=newspaper_id)

    def search_articles(
        self,
        search: str | None = None,
        owner_id: int | None = None,
        newspaper_id: int | None = None,
        order_by_popularity: bool = False,
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
                COALESCE(f.popularity, 0) AS popularity,
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
            LEFT JOIN (
                SELECT article_id, COUNT(*) AS popularity
                FROM article_favorites
                GROUP BY article_id
            ) AS f ON f.article_id = a.id
            """
        ]
        if clauses:
            sql.append("WHERE " + " AND ".join(clauses))
        if order_by_popularity:
            sql.append("ORDER BY COALESCE(f.popularity, 0) DESC, a.created_at DESC")
        else:
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
                COALESCE(f.popularity, 0) AS popularity,
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
            LEFT JOIN (
                SELECT article_id, COUNT(*) AS popularity
                FROM article_favorites
                GROUP BY article_id
            ) AS f ON f.article_id = a.id
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

    def get_related_articles(self, article_id: int, limit: int = 10) -> list[ArticleRow]:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                """
                WITH target_newspapers AS (
                    SELECT na.newspaper_id
                    FROM newspaper_articles AS na
                    WHERE na.article_id = %s
                ),
                scored_related AS (
                    SELECT
                        a.id,
                        a.title,
                        a.content,
                        a.url,
                        a.owner_id,
                        COALESCE(f.popularity, 0) AS popularity,
                        a.created_at,
                        a.updated_at,
                        COUNT(DISTINCT na.newspaper_id) AS overlap_count
                    FROM articles AS a
                    JOIN newspaper_articles AS na ON na.article_id = a.id
                    LEFT JOIN (
                        SELECT article_id, COUNT(*) AS popularity
                        FROM article_favorites
                        GROUP BY article_id
                    ) AS f ON f.article_id = a.id
                    WHERE na.newspaper_id IN (SELECT newspaper_id FROM target_newspapers)
                      AND a.id <> %s
                    GROUP BY a.id, a.title, a.content, a.url, a.owner_id, a.created_at, a.updated_at, f.popularity
                )
                SELECT
                    sr.id,
                    sr.title,
                    sr.content,
                    sr.url,
                    sr.owner_id,
                    sr.popularity,
                    sr.created_at,
                    sr.updated_at,
                    COALESCE(
                        ARRAY(
                            SELECT na2.newspaper_id
                            FROM newspaper_articles AS na2
                            WHERE na2.article_id = sr.id
                            ORDER BY na2.newspaper_id
                        ),
                        ARRAY[]::INTEGER[]
                    ) AS newspaper_ids
                FROM scored_related AS sr
                ORDER BY sr.overlap_count DESC, sr.popularity DESC, sr.created_at DESC
                LIMIT %s
                """,
                (article_id, article_id, limit),
            )
            rows = cur.fetchall()

        result: list[ArticleRow] = []
        for row in rows:
            article = self.row_to_article(row)
            if article is not None:
                result.append(article)
        return result

    def add_article_favorite(self, user_id: int, article_id: int) -> ArticleRow | None:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO article_favorites (user_id, article_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (user_id, article_id),
            )
            return self.fetch_article(cur, article_id)

    def remove_article_favorite(self, user_id: int, article_id: int) -> ArticleRow | None:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM article_favorites
                WHERE user_id = %s AND article_id = %s
                """,
                (user_id, article_id),
            )
            return self.fetch_article(cur, article_id)

    def list_favorite_articles(self, user_id: int) -> list[ArticleRow]:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    a.id,
                    a.title,
                    a.content,
                    a.url,
                    a.owner_id,
                    COALESCE(f.popularity, 0) AS popularity,
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
                JOIN article_favorites AS af ON af.article_id = a.id AND af.user_id = %s
                LEFT JOIN (
                    SELECT article_id, COUNT(*) AS popularity
                    FROM article_favorites
                    GROUP BY article_id
                ) AS f ON f.article_id = a.id
                ORDER BY af.created_at DESC
                """,
                (user_id,),
            )
            rows = cur.fetchall()

        result: list[ArticleRow] = []
        for row in rows:
            article = self.row_to_article(row)
            if article is not None:
                result.append(article)
        return result

    def add_read_later(self, user_id: int, article_id: int) -> ArticleRow | None:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO article_read_later (user_id, article_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (user_id, article_id),
            )
            return self.fetch_article(cur, article_id)

    def remove_read_later(self, user_id: int, article_id: int) -> ArticleRow | None:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM article_read_later
                WHERE user_id = %s AND article_id = %s
                """,
                (user_id, article_id),
            )
            return self.fetch_article(cur, article_id)

    def list_read_later_articles(self, user_id: int) -> list[ArticleRow]:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    a.id,
                    a.title,
                    a.content,
                    a.url,
                    a.owner_id,
                    COALESCE(f.popularity, 0) AS popularity,
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
                JOIN article_read_later AS arl ON arl.article_id = a.id AND arl.user_id = %s
                LEFT JOIN (
                    SELECT article_id, COUNT(*) AS popularity
                    FROM article_favorites
                    GROUP BY article_id
                ) AS f ON f.article_id = a.id
                ORDER BY arl.created_at DESC
                """,
                (user_id,),
            )
            rows = cur.fetchall()

        result: list[ArticleRow] = []
        for row in rows:
            article = self.row_to_article(row)
            if article is not None:
                result.append(article)
        return result

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
                COALESCE(f.popularity, 0) AS popularity,
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
            LEFT JOIN (
                SELECT article_id, COUNT(*) AS popularity
                FROM article_favorites
                GROUP BY article_id
            ) AS f ON f.article_id = a.id
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

    # ---- Sources management ----
    def create_source(
        self,
        name: str,
        feed_url: str | None,
        description: str | None,
        status: str = "active",
    ) -> SourceRow:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sources (name, feed_url, description, status)
                VALUES (%s, %s, %s, %s)
                RETURNING id, name, feed_url, description, status, created_at, updated_at
                """,
                (name, feed_url, description, status),
            )
            row = cur.fetchone()
        if row is None:
            raise RuntimeError("Failed to create source.")
        source = self.row_to_source(row)
        if source is None:
            raise RuntimeError("Failed to map created source.")
        return source

    def list_sources(
        self,
        search: str | None = None,
        status: str | None = None,
        follower_id: int | None = None,
    ) -> list[SourceRow]:
        clauses: list[str] = []
        params: list[Any] = []

        if status:
            clauses.append("s.status = %s")
            params.append(status)

        pattern: str | None = None
        if search:
            trimmed = search.strip()
            if trimmed:
                pattern = f"%{trimmed}%"
                clauses.append("(s.name ILIKE %s OR s.description ILIKE %s)")
                params.extend([pattern, pattern])

        sql = [
            """
            SELECT
                s.id,
                s.name,
                s.feed_url,
                s.description,
                s.status,
                s.created_at,
                s.updated_at
            """,
        ]
        if follower_id is not None:
            sql.append(
                """
                , CASE WHEN uf.user_id IS NULL THEN FALSE ELSE TRUE END AS is_followed
                """
            )
        sql.append("FROM sources AS s")
        if follower_id is not None:
            sql.append(
                """
                LEFT JOIN user_followed_sources AS uf
                    ON uf.source_id = s.id AND uf.user_id = %s
                """
            )
            params.insert(0, follower_id)
        if clauses:
            sql.append("WHERE " + " AND ".join(clauses))
        sql.append("ORDER BY s.created_at DESC")

        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute("\n".join(sql), tuple(params))
            rows = cur.fetchall()

        results: list[SourceRow] = []
        for row in rows:
            source = self.row_to_source(row)
            if source is not None:
                results.append(source)
        return results

    # ---- Notifications ----
    def create_notifications_for_source_followers(
        self,
        source_id: int,
        message: str,
        article_id: int | None = None,
        newspaper_id: int | None = None,
    ) -> int:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO notifications (user_id, source_id, article_id, newspaper_id, message)
                SELECT uf.user_id, %s, %s, %s, %s
                FROM user_followed_sources AS uf
                WHERE uf.source_id = %s
                """,
                (source_id, article_id, newspaper_id, message, source_id),
            )
            return cur.rowcount

    def list_notifications(self, user_id: int, include_read: bool = False) -> list[NotificationRow]:
        clauses = ["user_id = %s"]
        params: list[Any] = [user_id]
        if not include_read:
            clauses.append("is_read = FALSE")
        sql = [
            """
            SELECT id, user_id, source_id, article_id, newspaper_id, message, is_read, created_at
            FROM notifications
            WHERE """
            + " AND ".join(clauses),
            "ORDER BY created_at DESC",
        ]
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute("\n".join(sql), tuple(params))
            rows = cur.fetchall()
        result: list[NotificationRow] = []
        for row in rows:
            notification = self.row_to_notification(row)
            if notification is not None:
                result.append(notification)
        return result

    def mark_notification_read(self, user_id: int, notification_id: int) -> NotificationRow | None:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE notifications
                SET is_read = TRUE
                WHERE id = %s AND user_id = %s
                RETURNING id, user_id, source_id, article_id, newspaper_id, message, is_read, created_at
                """,
                (notification_id, user_id),
            )
            row = cur.fetchone()
        return self.row_to_notification(row)

    def get_source(self, source_id: int, follower_id: int | None = None) -> SourceRow | None:
        with self._connection_factory() as conn, conn.cursor() as cur:
            if follower_id is None:
                cur.execute(
                    """
                    SELECT id, name, feed_url, description, status, created_at, updated_at
                    FROM sources
                    WHERE id = %s
                    """,
                    (source_id,),
                )
            else:
                cur.execute(
                    """
                    SELECT
                        s.id,
                        s.name,
                        s.feed_url,
                        s.description,
                        s.status,
                        s.created_at,
                        s.updated_at,
                        CASE WHEN uf.user_id IS NULL THEN FALSE ELSE TRUE END AS is_followed
                    FROM sources AS s
                    LEFT JOIN user_followed_sources AS uf
                        ON uf.source_id = s.id AND uf.user_id = %s
                    WHERE s.id = %s
                    """,
                    (follower_id, source_id),
                )
            row = cur.fetchone()
        return self.row_to_source(row)

    def update_source(
        self,
        source_id: int,
        name: str | None,
        feed_url: str | None,
        description: str | None,
        status: str | None,
    ) -> SourceRow | None:
        assignments: list[str] = []
        params: list[Any] = []

        if name is not None:
            assignments.append("name = %s")
            params.append(name)
        if feed_url is not None:
            assignments.append("feed_url = %s")
            params.append(feed_url)
        if description is not None:
            assignments.append("description = %s")
            params.append(description)
        if status is not None:
            assignments.append("status = %s")
            params.append(status)

        set_clause = ", ".join(assignments)
        if set_clause:
            set_clause = f"{set_clause}, "

        params.append(source_id)

        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE sources
                SET {set_clause}updated_at = NOW()
                WHERE id = %s
                RETURNING id, name, feed_url, description, status, created_at, updated_at
                """,
                tuple(params),
            )
            row = cur.fetchone()
        return self.row_to_source(row)

    def follow_source(self, user_id: int, source_id: int) -> SourceRow | None:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_followed_sources (user_id, source_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (user_id, source_id),
            )
            return self.get_source(source_id, follower_id=user_id)

    def unfollow_source(self, user_id: int, source_id: int) -> SourceRow | None:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM user_followed_sources
                WHERE user_id = %s AND source_id = %s
                """,
                (user_id, source_id),
            )
            return self.get_source(source_id, follower_id=user_id)

    def list_followed_sources(self, user_id: int) -> list[SourceRow]:
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    s.id,
                    s.name,
                    s.feed_url,
                    s.description,
                    s.status,
                    s.created_at,
                    s.updated_at,
                    TRUE AS is_followed
                FROM user_followed_sources AS uf
                JOIN sources AS s ON s.id = uf.source_id
                WHERE uf.user_id = %s
                ORDER BY uf.created_at DESC
                """,
                (user_id,),
            )
            rows = cur.fetchall()

        results: list[SourceRow] = []
        for row in rows:
            source = self.row_to_source(row)
            if source is not None:
                results.append(source)
        return results
