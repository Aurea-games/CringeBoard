# CringeBoard

CringeBoard is a Flipboard‑like content aggregation app with a FastAPI backend and a React (Vite) frontend. This repository includes a complete Docker setup for local development, a scheduler placeholder for feed aggregation, and documentation in French and English.

## Quick Start
- Prerequisites: Docker Desktop or Docker Engine + docker compose v2
- Production-like stack (build once, immutable containers): `docker compose up -d`
- Development stack with live reload (bind mounts): `docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build`
- With pgAdmin and worker in dev: add `--profile devtools --profile worker` to either command
- Access:
  - Web: http://localhost:3000
  - API: http://localhost:8000/healthz
  - pgAdmin: http://localhost:5050

See full Docker guides below for details.

## Documentation Index
- Project specification (EN): [Doc/Specification_document_EN.md](Doc/Specification_document_EN.md)
- Cahier des charges (FR): [Doc/Cahier_des_charges_FR.md](Doc/Cahier_des_charges_FR.md)
- Docker guide (FR): [Doc/Guide_Docker_FR.md](Doc/Guide_Docker_FR.md)
- Docker guide (EN): [Doc/Guide_Docker_EN.md](Doc/Guide_Docker_EN.md)

## Repository Layout
- Backend (FastAPI): `backend/`
- Frontend (React + Vite): `frontend/`
- Compose + infra: `docker-compose.yml`, `.env`, `pgadmin/servers.json`

## Environment
- Configure local settings in `.env` (see `.env.example`).
- Default credentials are intended for local dev only; change for production.

## Notes
- Images use latest stable bases (alpine/latest); rebuild with `--no-cache` after updates.
- The scheduler (`worker` profile) is a placeholder loop that you can extend for feed aggregation.

---
Happy hacking!
