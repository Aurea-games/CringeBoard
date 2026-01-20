# Security Review — Auth & Config (passwords, tokens, CORS, secrets)

Scope: backend auth flow (`app/api/routes/auth`), CORS setup (`app/main.py`, `app/core/config.py`), and secret handling (.env, compose).

## Findings

- **High — Tokens stored plaintext, no expiry/rotation**  
  - Access/refresh tokens are random (`secrets.token_urlsafe`) but persisted as raw strings in `tokens.token` with no `expires_at`. Refresh tokens never expire and are not rotated; access tokens are long-lived and indistinguishable from refresh tokens. Lost DB backups or read access expose all sessions.  
  - Recommendation: hash tokens before storage (e.g., SHA-256 of the token; only return the cleartext once), add `created_at`/`expires_at`, enforce short-lived access (≈15–30 min) and longer refresh (≈30–60 days) with rotation on refresh. Consider JWT with signed expiry if you prefer stateless access tokens; keep refresh server-side and hashed. Invalidate on logout and periodically purge expired rows.

- **Medium — Password hashing policy not parameterized**  
  - Uses bcrypt with default cost; no global pepper; minimum length is only 8 chars and no common-password checks; login lacks rate limiting. Aggregator service auto-creates a user using `AGGREGATOR_USER_PASSWORD` with default `change-me`.  
  - Recommendation: configure bcrypt cost via env (e.g., `BCRYPT_ROUNDS`) and document the chosen cost; enforce stronger password policy (min 12 chars, deny common/known-breached passwords), add rate limiting/lockout/backoff on login/refresh, and optionally add an application-wide pepper (from `SECRET_KEY`) to hashes. Require production values for `AGGREGATOR_USER_*` or create that account via migration instead of at runtime.

- **Medium — CORS broadly permissive with credentials**  
  - `allow_credentials=True` with `allow_methods=["*"]` and `allow_headers=["*"]`; origins come from `CORS_ORIGINS` (default `http://localhost:3000`). Misconfiguration could expose cookies/authorization to unwanted origins.  
  - Recommendation: set explicit origins per environment, disable `allow_credentials` if using bearer tokens, and narrow methods/headers to what the API uses. Consider rejecting empty `CORS_ORIGINS` to avoid accidental open CORS.

- **Medium — Secrets management defaults are weak**  
  - `.env.example` includes weak defaults (`SECRET_KEY`, DB/passwords, aggregator password) and `SECRET_KEY` is unused. Tokens rely solely on randomness without a signing secret. No mention of secret storage for production (Docker secrets/secret manager).  
  - Recommendation: require strong, unique secrets per environment; document secret sourcing (e.g., Docker/Swarm/K8s secrets, cloud secret manager, or GH Actions env for builds). Remove default `change-me` values in production config, ensure `.env` is never committed with real secrets, and use `SECRET_KEY` to sign/pepper tokens or crypto operations.

## Suggested next steps (order of impact)
1) Implement token hashing + expiry/rotation; add `expires_at` columns and purge job. Use JWT for access if desired; keep hashed refresh tokens server-side.  
2) Harden password policy: configurable bcrypt cost, stronger length/common-password checks, and login rate limiting/backoff. Set production-only aggregator credentials or migrate the account instead of runtime creation.  
3) Tighten CORS per environment; consider `allow_credentials=False` and scoped methods/headers. Fail fast if `CORS_ORIGINS` is empty.  
4) Define a secrets policy: strong defaults, production sourcing via secret manager, rotate `SECRET_KEY`/DB creds, and document operational handling in deployment guides.  
5) (Optional) Add security tests/checks (e.g., unit tests for token expiry/rotation, lint to block empty CORS origins, and CI secret scanners).
