# Deploying TalentLens for free

This is a $0 deployment of the full stack, using managed free tiers in place
of the containers `infra/docker-compose.yml` runs locally. Local dev is
unaffected — this doc and the files it references (`render.yaml`,
`backend/scripts/start.sh`) are deploy-only additions.

| Local (docker-compose) | Free hosting |
|---|---|
| `postgres` (pgvector) | [Supabase](https://supabase.com) free Postgres project |
| `redis` | [Upstash](https://upstash.com) free Redis database |
| `minio` | [Cloudflare R2](https://developers.cloudflare.com/r2/) free bucket |
| `backend` + `worker` | [Render](https://render.com) free Web Service (runs both — see below) |
| `frontend` | [Vercel](https://vercel.com) free project |
| LLM | [Groq](https://console.groq.com) free API key |

**Why backend + worker share one Render service:** Render's free plan has no
"Background Worker" service type (paid-only). `backend/scripts/start.sh`
starts the Celery worker as a background process and `uvicorn` as the
foreground process in the same container, so both fit in the one free web
service. This is a deploy-time-only arrangement.

## 1. Provision the free resources

1. **Supabase** — new project → SQL Editor → `create extension if not exists vector;`
   → Project Settings → Database → copy the connection string (use the
   pooled "Transaction" connection string for `DATABASE_URL`, and the direct
   connection for `DATABASE_URL_SYNC`, which Alembic uses).
2. **Upstash** — new Redis database → copy the `rediss://` connection URL.
   Reuse the same URL for `REDIS_URL`, `CELERY_BROKER_URL`, and
   `CELERY_RESULT_BACKEND` by appending `/0`, `/1`, `/2` respectively (same
   split as `infra/docker-compose.yml`).
3. **Cloudflare R2** — create a bucket (e.g. `talentlens-resumes`) → create
   an API token (Account API Token, Object Read & Write) → note the
   Account ID; the S3 endpoint is
   `https://<account_id>.r2.cloudflarestorage.com`.
4. **Groq** — create an API key at console.groq.com.
5. **Render** — New → Blueprint → connect this GitHub repo → Render reads
   `render.yaml` at the repo root and creates the `talentlens-backend`
   service. After the first deploy, open the service → Environment → fill
   in the secrets listed below.
6. **Vercel** — New Project → import this repo → set **Root Directory** to
   `frontend` → add the `NEXT_PUBLIC_API_URL` env var (the Render service's
   URL + `/api/v1`, e.g. `https://talentlens-backend.onrender.com/api/v1`).

## 2. Render environment variables

Set these in the Render dashboard (not in `render.yaml`, which only lists
their names — they're secrets):

| Var | Value |
|---|---|
| `JWT_SECRET` | `python3 -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `DATABASE_URL` | Supabase pooled connection string, `postgresql+asyncpg://...?ssl=require` |
| `DATABASE_URL_SYNC` | Supabase direct connection string, `postgresql+psycopg2://...?sslmode=require` |
| `REDIS_URL` / `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | Upstash URL with `/0`, `/1`, `/2` suffixes |
| `S3_ENDPOINT` | `https://<account_id>.r2.cloudflarestorage.com` |
| `S3_BUCKET` | your R2 bucket name |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | R2 API token key/secret |
| `GROQ_API_KEY` | your Groq key |
| `CORS_ORIGINS` | your Vercel URL, e.g. `https://talentlens.vercel.app` |

`ssl=require` / `sslmode=require` are needed because Supabase requires TLS —
without it the connection is rejected.

## 3. GitHub Actions (CI + auto-deploy)

- `.github/workflows/ci.yml` runs backend `ruff`/`pytest` and frontend
  `lint`/`build` on every push and PR.
- `.github/workflows/deploy.yml` fires after CI succeeds on `main` and hits
  Render's deploy hook. Get the hook URL from the Render service → Settings
  → Deploy Hook, and add it as a repo secret named `RENDER_DEPLOY_HOOK_URL`
  (Settings → Secrets and variables → Actions).
- Vercel deploys the frontend itself via its native GitHub integration —
  no Action needed for that side.

## 4. First deploy checklist

1. Push to `main` (or re-run the Render/Vercel first deploy manually).
2. Confirm the Render logs show `alembic upgrade head` succeeding, then the
   Celery worker and uvicorn both starting.
3. Visit the Vercel URL → Register → create an organization + admin user.
4. Upload a resume, confirm it reaches "processed" (proves the worker is
   running), create a job, run a match.

## Known free-tier limitations

- **Render free service sleeps after 15 min idle** — first request after
  that takes 30–60s to cold-start.
- **Supabase free project pauses after 7 days with zero API calls** —
  auto-resumes on the next request within about a minute.
- **Upstash free Redis has a daily command cap** — fine for low-traffic demo
  use, not for real production load.
- Running the Celery worker in the same container as the API means a slow
  LLM call or a large resume batch can compete with the API for CPU/memory
  on Render's free 512MB instance — acceptable for a demo, not how you'd
  run this at real scale (that's what the two-service `docker-compose`
  setup and a paid Render worker are for).
