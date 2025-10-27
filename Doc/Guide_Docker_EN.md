# Docker Guide — CringeBoard

This guide explains how to start the Docker environment (API, Frontend, Postgres, Redis), use pgAdmin to view the database, and manage profiles/volumes.

## 1) Prerequisites

- Docker Desktop (Windows/macOS) or Docker Engine + docker compose v2
- Free ports: `3000` (web), `8000` (API), `5432` (Postgres), `6379` (Redis), `5050` (pgAdmin)

## 2) Service Structure

- `db` — PostgreSQL
- `redis` — Redis (cache / queue)
- `api` — FastAPI backend (Uvicorn)
- `web` — React frontend (Vite dev server)
- `scheduler` — Scheduled task (feed aggregation)
- `pgadmin` — Postgres admin UI

## 3) Environment Variables

A `.env` file is provided (see `.env.example`). Key variables:

- `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD`
- `API_PORT` / `WEB_PORT` / `PGADMIN_PORT` / `REDIS_PORT`
- `CORS_ORIGINS` (CORS origins on the API side)
- `VITE_API_BASE_URL` (API base URL on the frontend side)

Edit `.env` if needed, then run `docker compose up -d` again.

## 4) Quick Start

- Production-like stack (immutable containers): `docker compose up -d`
- Development stack with bind mounts: `docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build`

Access:

- Frontend: http://localhost:3000
- API: http://localhost:8000/healthz
- pgAdmin: http://localhost:5050 (credentials in `.env`)

## 5) Use pgAdmin to View the Database

Initial login:

1. Open http://localhost:5050
2. Log in with `PGADMIN_DEFAULT_EMAIL` and `PGADMIN_DEFAULT_PASSWORD` (see `.env`).

### 5.1) Manually Add a Postgres Server

In pgAdmin: right‑click "Servers" → "Create" → "Server…"

- General tab
  - Name: `CringeBoard DB`
- Connection tab
  - Host name/address: `db`
  - Port: (POSTGRES_PORT)
  - Maintenance database: (POSTGRES_DB)
  - Username: (POSTGRES_USER)
  - Password: (POSTGRES_PASSWORD)
  - Save Password: checked

Save. You can then browse: Databases → cringeboard → Schemas → public → Tables.

### 5.2) Auto Pre‑Configuration (servers.json) — Recommended

The repository contains `pgadmin/servers.json`. It is mounted automatically on first start to create the "CringeBoard DB" entry. The password is not stored in this file: enter it once; it will be remembered (pgAdmin persistent volume). You should edit this file before launching Docker.

If you add/modify `servers.json` after a first run, recreate pgAdmin:

```
docker compose rm -sf pgadmin
docker compose up -d pgadmin
```

## 6) Useful Commands

- View status: `docker compose ps`
- Service logs: `docker compose logs -f api` (or `web`, `db`, `pgadmin`, …)
- Stop: `docker compose down`
- Stop and remove volumes: `docker compose down -v`
- Full rebuild (new Dockerfiles/images):
  - `docker compose build --no-cache`
  - `docker compose up -d`

## 7) Volumes and Persistence

- `pgdata`: PostgreSQL data
- `redisdata`: Redis data
- `pgadmindata`: pgAdmin config/state (saved servers, encrypted passwords)

To start from a "clean slate," add `-v` to `down` (also removes volumes). Warning: this erases data.

## 8) Development

- Use the additional compose file: `docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build`
- The API mounts the backend sources and runs Uvicorn with `--reload`.
- The frontend mounts the Vite project and runs the dev server.
- Edits on the host are available instantly inside the containers.

## 9) Troubleshooting (FAQ)

**Port already in use**: change the port in `.env` (e.g., `API_PORT=8001`) then `docker compose up -d`.

**pgAdmin can't see Postgres**: ensure `db` is healthy (`docker compose ps`), then retry. Host must be `db` (not `localhost`).

**psycopg2 / Python 3.13 error**: the project uses `psycopg[binary]` (v3) and `postgresql+psycopg://` in `DATABASE_URL` for compatibility with Python 3.13.

**"latest"/"alpine" image changes**: a `build --no-cache` may be required after base‑image updates.

## 10) Security (Local)

- Secrets in `.env` are for local use. Change `POSTGRES_PASSWORD` and `SECRET_KEY` for production.
- Restrict `CORS_ORIGINS` if exposed.

---

Happy programming !
