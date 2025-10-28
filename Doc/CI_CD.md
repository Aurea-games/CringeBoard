# CI/CD Overview

CringeBoard is equipped with a GitHub Actions–based CI/CD pipeline that covers backend validation, frontend validation, and automated Docker image publication.

## Workflows

### Backend CI (`.github/workflows/backend-ci.yml`)
- **Trigger**: pushes and pull requests touching `backend/**`.
- **Steps**:
  - Install Python 3.12 with dependency caching.
  - Install runtime (`requirements.txt`) and tooling (`requirements-dev.txt`) packages.
  - Run `ruff check app` and `black --check app`.
  - Placeholder step for future pytest runs (disabled until tests exist).

### Frontend CI (`.github/workflows/frontend-ci.yml`)
- **Trigger**: pushes and pull requests touching `frontend/**`.
- **Steps**:
  - Install Node.js 20 with npm cache.
  - Run `npm ci`.
  - Execute `npm run lint`, `npm run format:check`, and `npm run build`.

### Docker Images (`.github/workflows/docker-publish.yml`)
- **Trigger**: pushes to `main`, Git tags matching `v*`, or manual dispatch.
- **Steps**:
  - Build the backend (`backend/Dockerfile`) and frontend (`frontend/Dockerfile`) images.
  - Publish to GHCR as `ghcr.io/<owner>/cringeboard-backend` and `ghcr.io/<owner>/cringeboard-frontend`.
  - Tag strategy:
    - `latest` on the default branch.
    - Branch name tags.
    - Semantic tags for Git releases (`v*`).
    - Short SHA tag for traceability.
  - Layer caching via GitHub Actions cache.

## Required Secrets and Permissions

| Secret / Permission | Workflow(s) | Purpose |
| --- | --- | --- |
| `GITHUB_TOKEN` (default) with `packages: write` | Docker Images | Authenticate to GHCR. |

All workflows rely solely on repository files; no additional secrets are currently required.

## Extensibility

- **Backend tests**: enable the pytest step once test suites are in place.
- **Environment-specific deploys**: add additional jobs depending on the branch (e.g., staging vs prod).
- **Security scanning**: integrate tools such as Trivy or Dependabot for vulnerability scanning.

---

For quick reference, see the “Code Quality” and “CI/CD” sections in `README.md`.
