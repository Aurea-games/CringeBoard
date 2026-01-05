# Database Schema — CringeBoard

This document summarizes the relational schema created at backend startup (`backend/app/core/db.py::ensure_schema`). The API uses PostgreSQL (URL from `DATABASE_URL`), psycopg3, and creates tables if they do not exist.

## Entity Overview
- **users**: local accounts; own newspapers and articles; own preferences.
- **tokens**: auth tokens bound to a user.
- **sources**: content sources (RSS/Flipboard/etc.), optionally linked to newspapers; followed by users.
- **newspapers**: user-created collections; can reference a `source` and be public via `public_token`.
- **articles**: content items owned by a user; can be favorited, marked read-later, and attached to newspapers.
- **article_favorites / article_read_later**: per-user flags for articles.
- **newspaper_articles**: junction table between newspapers and articles.
- **user_preferences**: theme and hidden source IDs per user.
- **user_followed_sources**: which sources each user follows.
- **notifications**: messages tying users to source/article/newspaper events.

## Tables & Columns

### users
| Column | Type | Notes |
| --- | --- | --- |
| id | serial PK | |
| email | text | unique, indexed (`ix_users_email`) |
| password_hash | text | hashed password |
| created_at | timestamptz | default now |
| updated_at | timestamptz | default now |

### tokens
| Column | Type | Notes |
| --- | --- | --- |
| token | text PK | |
| token_type | text | |
| user_id | int FK users.id | cascade delete, indexed (`ix_tokens_user_id`) |
| created_at | timestamptz | default now |

### sources
| Column | Type | Notes |
| --- | --- | --- |
| id | serial PK | |
| name | text | unique (case-insensitive index `ix_sources_name`) |
| feed_url | text | nullable |
| description | text | nullable |
| status | text | default `active` |
| created_at | timestamptz | default now |
| updated_at | timestamptz | default now |

### newspapers
| Column | Type | Notes |
| --- | --- | --- |
| id | serial PK | |
| title | text | not null |
| description | text | nullable |
| owner_id | int FK users.id | cascade delete, indexed (`ix_newspapers_owner_id`) |
| is_public | boolean | default false |
| public_token | text | unique nullable token for sharing |
| source_id | int FK sources.id | on delete set null |
| created_at | timestamptz | default now |
| updated_at | timestamptz | default now |

### articles
| Column | Type | Notes |
| --- | --- | --- |
| id | serial PK | |
| title | text | not null |
| content | text | nullable |
| url | text | nullable |
| owner_id | int FK users.id | cascade delete, indexed (`ix_articles_owner_id`) |
| created_at | timestamptz | default now |
| updated_at | timestamptz | default now |

### article_favorites
| Column | Type | Notes |
| --- | --- | --- |
| user_id | int FK users.id | cascade delete |
| article_id | int FK articles.id | cascade delete, indexed (`ix_article_favorites_article_id`) |
| created_at | timestamptz | default now |
| PK | (user_id, article_id) | |

### article_read_later
| Column | Type | Notes |
| --- | --- | --- |
| user_id | int FK users.id | cascade delete, indexed (`ix_article_read_later_user_id`) |
| article_id | int FK articles.id | cascade delete, indexed (`ix_article_read_later_article_id`) |
| created_at | timestamptz | default now |
| PK | (user_id, article_id) | |

### newspaper_articles
| Column | Type | Notes |
| --- | --- | --- |
| newspaper_id | int FK newspapers.id | cascade delete |
| article_id | int FK articles.id | cascade delete, indexed (`ix_newspaper_articles_article_id`) |
| created_at | timestamptz | default now |
| PK | (newspaper_id, article_id) | |

### user_preferences
| Column | Type | Notes |
| --- | --- | --- |
| user_id | int PK FK users.id | cascade delete |
| theme | text | default `light`, indexed (`ix_user_preferences_theme`) |
| hidden_source_ids | int[] | default empty array |
| updated_at | timestamptz | default now |

### user_followed_sources
| Column | Type | Notes |
| --- | --- | --- |
| user_id | int FK users.id | cascade delete |
| source_id | int FK sources.id | cascade delete, indexed (`ix_user_followed_sources_source_id`) |
| created_at | timestamptz | default now |
| PK | (user_id, source_id) | |

### notifications
| Column | Type | Notes |
| --- | --- | --- |
| id | serial PK | |
| user_id | int FK users.id | cascade delete, part of index (`ix_notifications_user_id_created`) |
| source_id | int FK sources.id | cascade delete |
| article_id | int FK articles.id | cascade delete, nullable |
| newspaper_id | int FK newspapers.id | cascade delete, nullable |
| message | text | not null |
| is_read | boolean | default false |
| created_at | timestamptz | default now, in index (`ix_notifications_user_id_created`) |

## Relationships (summarized)
- One user → many tokens, newspapers, articles, notifications.
- One user ↔ many articles via favorites and read-later junction tables.
- One user ↔ many sources via `user_followed_sources`.
- One source → many newspapers; one source → many notifications.
- One article ↔ many newspapers via `newspaper_articles`.
- One newspaper → many notifications.
- One user → one preferences row (`user_preferences` PK = `user_id`).

## Operational Notes
- Schema is created at runtime (idempotent); migrations are not yet managed by Alembic.
- Default data retention/purging is not implemented; cleanup must be manual.
- Adding new columns/tables should follow a migration path; if you extend `ensure_schema`, prefer non-breaking `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` to keep backward compatibility.
