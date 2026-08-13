# API documentation

The backend is FastAPI, which means interactive API docs are generated
automatically from the code — nothing to keep in sync by hand:

| What | Where (once `docker compose up`, i.e. backend on :8000) |
|---|---|
| Swagger UI (try requests in the browser) | http://localhost:8000/docs |
| ReDoc (readable reference) | http://localhost:8000/redoc |
| Raw OpenAPI 3.1 spec (JSON) | http://localhost:8000/openapi.json |

A snapshot of the spec is also checked into this repo for offline reference
and Postman import:

- [`docs/api/openapi.json`](api/openapi.json) — full spec, 21 endpoints.
- [`docs/api/postman_collection.json`](api/postman_collection.json) — a
  Postman v2.1 collection generated from the spec above (import it directly
  into Postman/Insomnia). Grouped into folders by tag (`auth`, `jobs`,
  `resumes`, `candidates`, `rankings`, `search`, `health`).
- [`docs/api/generate_postman.py`](api/generate_postman.py) — regenerates
  the Postman collection from `openapi.json`. Re-run both steps (see the
  docstring at the top of that script) whenever an endpoint changes.

## Authentication

Every endpoint except `POST /auth/register`, `POST /auth/login`, and the
two `/health*` routes requires a JWT bearer token:

```
Authorization: Bearer <access_token>
```

1. `POST /api/v1/auth/register` with `{organization_name, email, password, name}`
   creates a **new organization** and its first `ADMIN` user in one call —
   there's no separate "create org" step.
2. `POST /api/v1/auth/login` with `{email, password}` returns
   `{access_token, token_type, user}`.
3. In the Postman collection, set the collection variable `token` to that
   `access_token` (or use the `auth/login` request's response and a
   [Postman post-response script](https://learning.postman.com/docs/tests-and-scripts/write-scripts/test-scripts/)
   to set it automatically) — every other request already inherits
   `Authorization: Bearer {{token}}` from the collection-level auth.

All data is **tenant-scoped by `organization_id`** (taken from the JWT, not
from the request body/params) — a token from one organization can never see
another organization's jobs/candidates/matches, enforced in every service
function, not just at the route layer.

## Endpoint groups

| Tag | Routes | Purpose |
|---|---|---|
| `auth` | register, login, me | Account + JWT issuance |
| `jobs` | CRUD, `POST /jobs/{id}/analyze` | Job postings + AI-assisted requirement extraction from the JD text |
| `resumes` | `POST /resumes/upload` (batch), status polling | Resume intake → async parse/extract/embed pipeline |
| `candidates` | list/get, pipeline status, notes, `POST /candidates/{id}/match/{job_id}` | Candidate records + recruiting pipeline + on-demand single match |
| `rankings` | `GET /jobs/{id}/ranking`, `GET /jobs/{id}/candidates`, `POST /jobs/{id}/recalculate` | Ranked candidate list for a job; bulk (re)matching |
| `search` | `POST /search/candidates` | Hybrid keyword (Postgres full-text) + semantic (pgvector) candidate search |
| `health` | liveness/readiness | Container healthchecks |

See `docs/architecture.md` for how a resume/job flows through these
endpoints end-to-end, and `docs/design-decisions.md` for why matching is
split into "on-demand single match" vs. "bulk recalculate" rather than
running automatically on every page view.
