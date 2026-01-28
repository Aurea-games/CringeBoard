# Tech Benchmark & Rationale

Scope: snapshot of why the current stack was chosen, with published benchmark signals and operational impact. Numbers come from upstream/public benchmarks (TechEmpower Round 21, Vite perf reports, Postgres/Redis perf notes) rather than local runs.

## Stack snapshot (high level)
| Layer | Selected tech | Benchmark signals | Alternatives & why not now |
| --- | --- | --- | --- |
| Frontend | React + TypeScript + Vite | Dev server cold start <1s and HMR ~50-200ms; prod builds 4-7s for medium apps; modern ESM output with smaller chunks vs legacy bundlers | Create React App (8-12s cold start, 25-45s builds); Next.js/Angular add SSR/opinionation we do not need yet |
| Backend | FastAPI + Uvicorn (async) | JSON serialization on async run: 35-45k RPS, p99 latency ~6-8ms; automatic OpenAPI docs | Express.js (20-25k RPS, higher p99 ~12-18ms); Django/Flask slower on sync stacks (8-12k RPS) |
| Database | PostgreSQL 16 (alpine) | TPC-B like OLTP: 90-110k TPS on 4 vCPU class; strong JSONB and FTS support reduces need for extra stores | MySQL 8: 70-90k TPS on similar workloads, weaker JSON indexes; MongoDB adds ops complexity |
| Cache | Redis 7 (alpine) | >150k ops/s with pipelining, sub-millisecond latency; keeps API p99 down vs hitting Postgres (40-80ms) for repeated reads | Relying only on DB adds latency and load; Memcached lacks richer data structures needed later |
| CI/CD | GitHub Actions + caches | Backend lint+tests typically 1.5-2.5 min; frontend lint+build 2-3 min with npm/pip caches; concurrency cancels stale runs | Self-hosted runners add maintenance; other SaaS CI similar but no marginal gain for current scope |
| Containers | Docker + Compose | Alpine bases keep images small (python:3.12-alpine ~60MB vs slim ~150MB; node:20-alpine ~50MB vs ~180MB); fast rebuilds with cached layers | Kubernetes/Helm premature for current footprint; heavier base images slow CI and dev loops |

## Frontend: React + Vite
- **Dev velocity**: Vite uses native ESM during dev, yielding sub-second cold starts and ~<200ms HMR for medium codebases (contrast: webpack/CRA often 800-1500ms and 8-12s cold boot).
- **Build throughput**: Rollup-based prod builds finish in ~4-7s for mid-size apps with code splitting; CRA/webpack equivalents are commonly 25-45s.
- **Bundle quality**: Out-of-the-box tree shaking, preloading hints, and CSS code-splitting reduce bundle sizes 10-30% vs legacy stacks, improving TTI on 3G/4G.
- **Fit**: SPA without SSR suits current routing; TypeScript keeps component contracts tight when wiring to the FastAPI schema.

## Backend: FastAPI + Uvicorn
- **Throughput & latency**: Async stack measured at ~35-45k RPS on JSON echo in TechEmpower; p99 latency typically 6-8ms. Express.js runs ~20-25k RPS; Django/Flask (sync) 8-12k RPS and higher tail latencies.
- **Cold start**: Uvicorn workers start in under a second on alpine images, useful for CI and container scaling.
- **Developer ergonomics**: Pydantic validation + type hints give strong compile-time guarantees and self-generated OpenAPI/Swagger docs, cutting manual API documentation effort.
- **Fit**: Async IO aligns with feed aggregation and future websockets; psycopg async driver and Redis client are first-class.

## Data layer: PostgreSQL 16 + Redis 7
- **PostgreSQL performance**: TPC-B style benches on 4 vCPU VMs show 90-110k TPS; JSONB with GIN indexes keeps query plans fast for document-like article payloads; built-in full-text search avoids an extra search service early on.
- **Redis as hot cache**: Single-node Redis regularly sustains 150k+ ops/s at <1ms p50 and <2ms p99; caching article lists or preferences can trim API tail latency by 30-60ms vs repeated DB hits.
- **Images**: `postgres:alpine` reduces image size and startup time; `redis:alpine` similar, which helps CI pulls and local dev.

## CI/CD: GitHub Actions
- **Speed**: With dependency caches, backend lint+tests typically finish in ~1.5-2.5 minutes; frontend lint+build in ~2-3 minutes. Concurrency cancellation keeps queues short during rebases.
- **Portability**: Workflow stays Linux-only and container-friendly; can be reproduced locally with `act` if needed.
- **Future headroom**: Easy to add matrix builds (Python 3.12/3.13), Trivy/Dependabot, or Docker publish without switching providers.

## Containers: Docker + Compose
- **Image footprint**: Alpine bases keep images ~2-3x smaller than slim/default bases (python:3.12-alpine ~60MB vs ~150MB; node:20-alpine ~50MB vs ~180MB). Smaller pulls improve CI and developer onboarding.
- **Startup**: Compose brings db+cache+api+web up in parallel; healthchecks gate the API on database readiness, reducing flakiness vs manual bootstraps.
- **Extendability**: Profiles already cover worker/pgadmin; can add `devtools` or `observability` profiles without changing deploy story.

## How to (re)measure locally
Use these repeatable steps to confirm the numbers on project hardware:
- **Backend RPS**: `hey -z 30s -c 50 http://localhost:8000/healthz` (or `k6 run` equivalent) after `docker compose up api`. Capture p50/p95/p99.
- **Cache impact**: Seed Redis with popular feed keys, rerun the same load with/without cache to compare tail latency.
- **Frontend build**: `cd frontend && npm run build -- --profile` to log bundle timings and sizes; compare to alternative configs if needed.
- **Database TPS**: `docker compose exec db pgbench -c 10 -T 60 -S` once schema exists; track TPS and latency before/after index tweaks.
- **CI timing**: Inspect GitHub Actions run durations; cache hits should keep total wall clock under ~5 minutes for the full pipeline.

## Recommendations
- Keep current stack; it balances high throughput with small images and fast dev loops.
- If we add SSR or heavier routing needs later, reevaluate Next.js/Remix; for search-heavy workloads consider Postgres FTS tuning before adding Elastic.
- Re-run the local benchmark set above after major dependency bumps (FastAPI/React/Node) or infra changes to validate regressions.
