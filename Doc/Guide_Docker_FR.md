# Guide Docker — CringeBoard

Ce guide explique comment démarrer l'environnement Docker (API, Frontend, Postgres, Redis), utiliser pgAdmin pour visualiser la base de données, et gérer les profils/volumes.

## 1) Prérequis

- Docker Desktop (Windows/macOS) ou Docker Engine + docker compose v2
- Ports libres: `3000` (web), `8000` (API), `5432` (Postgres), `6379` (Redis), `5050` (pgAdmin)

## 2) Structure des services

- `db` — PostgreSQL
- `redis` — Redis (cache / file d'attente)
- `api` — Backend FastAPI (Uvicorn)
- `web` — Frontend React (Vite dev server)
- `scheduler` — Tâche planifiée (agrégation de flux)
- `pgadmin` — UI d'administration Postgres

## 3) Variables d'environnement

Un fichier `.env` est fourni (voir `.env.example`). Principales variables:

- `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD`
- `API_PORT` / `WEB_PORT` / `PGADMIN_PORT` / `REDIS_PORT`
- `CORS_ORIGINS` (origines CORS côté API)
- `VITE_API_BASE_URL` (URL de base de l'API côté frontend)

Modifiez `.env` si nécessaire, puis relancez `docker compose up -d`.

## 4) Démarrage rapide

- Stack proche prod (conteneurs immuables): `docker compose up -d`
- Stack de développement (montage des sources): `docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build`

Accès:

- Frontend: http://localhost:3000
- API: http://localhost:8000/healthz
- pgAdmin: http://localhost:5050 (identifiants dans `.env`)

## 5) Utiliser pgAdmin pour voir la base

Connexion initiale:

1. Ouvrez http://localhost:5050
2. Connectez-vous avec `PGADMIN_DEFAULT_EMAIL` et `PGADMIN_DEFAULT_PASSWORD` (voir `.env`).

### 5.1) Ajout manuel d'un serveur Postgres

Dans pgAdmin: clic droit « Servers » → « Create » → « Server… »

- Onglet General
  - Name: `CringeBoard DB`
- Onglet Connection
  - Host name/address: `db`
  - Port: (POSTGRES_PORT)
  - Maintenance database: (POSTGRES_DB)
  - Username:  (POSTGRES_USER)
  - Password: (POSTGRES_PASSWORD)
  - Save Password: coché

Validez. Vous pouvez ensuite parcourir: Databases → cringeboard → Schemas → public → Tables.

### 5.2) Pré-configuration auto (servers.json) — recommandé

Le dépôt contient `pgadmin/servers.json`. Il est monté automatiquement au premier démarrage pour créer l'entrée « CringeBoard DB ». Le mot de passe n'est pas stocké dans ce fichier: entrez-le une fois; il sera mémorisé (volume persistant de pgAdmin). Vous devriez modifier ce fichier avant de lancer le docker

Si vous ajoutez/modifiez `servers.json` après un premier lancement, recréez pgAdmin:

```
docker compose rm -sf pgadmin
docker compose up -d pgadmin
```

## 6) Commandes utiles

- Voir l'état: `docker compose ps`
- Logs d'un service: `docker compose logs -f api` (ou `web`, `db`, `pgadmin`…)
- Arrêter: `docker compose down`
- Arrêter et supprimer volumes: `docker compose down -v`
- Rebuild complet (nouveaux Dockerfiles/images):
  - `docker compose build --no-cache`
  - `docker compose up -d`

## 7) Volumes et persistance

- `pgdata`: données PostgreSQL
- `redisdata`: données Redis
- `pgadmindata`: configuration/état pgAdmin (serveurs enregistrés, mots de passe chiffrés)

Pour repartir « propre », ajoutez `-v` à `down` (supprime aussi les volumes). Attention: cela efface les données.

## 8) Développement

- Utilisez le fichier compose additionnel: `docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build`
- L'API monte les sources backend et lance Uvicorn avec `--reload`.
- Le frontend monte le projet Vite et lance le serveur de dev.
- Les modifications locales sont visibles immédiatement dans les conteneurs.

## 9) Dépannage (FAQ)

**Port déjà utilisé**: changez le port dans `.env` (ex: `API_PORT=8001`) puis `docker compose up -d`.

**pgAdmin ne voit pas Postgres**: vérifiez que `db` est healthy (`docker compose ps`), puis re-tentez. Hôte doit être `db` (et non `localhost`).

**Erreur psycopg2 / Python 3.13**: le projet utilise `psycopg[binary]` (v3) et `postgresql+psycopg://` dans `DATABASE_URL` pour compatibilité avec Python 3.13.

**Changements d'images "latest"/"alpine"**: un `build --no-cache` peut être nécessaire après mise à jour des bases images.

## 10) Sécurité (local)

- Les secrets dans `.env` sont adaptés au local. Changez `POSTGRES_PASSWORD` et `SECRET_KEY` en production.
- Restreignez `CORS_ORIGINS` si exposé.

---

Bon développement !
