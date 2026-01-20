# CringeBoard Deployment & Environment

## Prerequisites
- Docker Desktop or Docker Engine with docker compose v2
- Free ports: 3000 (web), 8000 (API), 5432 (Postgres), 6379 (Redis), 5050 (pgAdmin)
- Optional for local parity: Python 3.12 + pip (backend), Node.js 20 + npm (frontend)

## Environment Setup
- Copy `.env.example` to `.env` and edit for your context
- Core: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `SECRET_KEY`, `ENV`
- Ports: `API_PORT`, `WEB_PORT`, `PGADMIN_PORT`, `REDIS_PORT`
- API CORS: `CORS_ORIGINS`
- Frontend API base: `VITE_API_BASE_URL` (URL reachable by the browser)
- Scheduler feeds: `FLIPBOARD_MAGAZINES`, `FLIPBOARD_ACCOUNTS`, `RSS_FEEDS`
- Volumes: `pgdata` (Postgres), `redisdata` (Redis), `pgadmindata` (pgAdmin). Removing them erases data.

## Development (Docker)
- Start with live reload: `docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build`
  - Services: Postgres, Redis, API (Uvicorn `--reload`), frontend (Vite dev), scheduler, pgAdmin
  - Access: web `http://localhost:3000`, API health `http://localhost:8000/healthz`, pgAdmin `http://localhost:5050`
- Stop/reset: `docker compose down` (keep data) or `./purge-dev.sh` (remove containers, images, volumes)
- Logs/status: `docker compose logs -f api` (or `web`, `db`, etc.), `docker compose ps`

## CI Parity (local checks)
- Backend: `pip install -r backend/requirements.txt -r backend/requirements-dev.txt`, then:
  - `ruff check backend/app`
  - `black --check backend/app`
  - `pytest` (exit 5 “no tests collected” is tolerated)
- Frontend (from `frontend/`): `npm ci`, then:
  - `npm run lint`
  - `npm run format:check`
  - `npm run build`
- Mirrors `.github/workflows/ci.yml`.

## Production-like Deployment
- Harden `.env`: strong DB password, unique `SECRET_KEY`, narrow `CORS_ORIGINS`, correct `VITE_API_BASE_URL`
- Build/run immutable stack: `docker compose up -d` (add `--build --no-cache` after base-image updates)
- Verify: `docker compose ps` health; API at `/healthz`
- Rolling update: `docker compose pull` (or `build --pull`) then `docker compose up -d`
- Backups: snapshot `pgdata` before migrations; don’t drop volumes unless you want a clean slate

## Troubleshooting
- Port in use: change ports in `.env`, rerun compose
- pgAdmin connection: host `db`, credentials from `.env`; if `pgadmin/servers.json` changes after first start, recreate pgAdmin with `docker compose rm -sf pgadmin && docker compose up -d pgadmin`
- Slow file change detection on Desktop: dev image already enables chokidar polling; ensure source mounts from `docker-compose.dev.yml`

## Security Notes
- `.env` defaults are local-only; never reuse in production
- Restrict `CORS_ORIGINS`; rotate `SECRET_KEY` when exposing publicly; manage DB credentials per environment
