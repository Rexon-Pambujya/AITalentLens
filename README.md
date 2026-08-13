# TalentLens AI

AI-assisted candidate intelligence for recruiters: upload resumes, extract
structured candidate profiles, score them against a job's requirements
across five weighted dimensions (skills, semantic relevance, experience,
education, projects), and get a recruiter-readable explanation of *why* —
grounded in computed facts, not an LLM's unchecked opinion. See
[`docs/design-decisions.md`](docs/design-decisions.md) for the reasoning
behind that split.

## Tech stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 14 (App Router), TanStack Query, Tailwind CSS, Recharts |
| Backend API | FastAPI, SQLAlchemy 2.x (async), Pydantic v2 |
| Async processing | Celery + Redis |
| Database | Postgres 16 + [pgvector](https://github.com/pgvector/pgvector) |
| Object storage | MinIO (S3-compatible) in Docker; local disk or real S3 elsewhere |
| AI | Pluggable provider — OpenAI, Groq, or local Ollama (`LLM_PROVIDER` env var) |

Full component/request-flow diagrams: [`docs/architecture.md`](docs/architecture.md).

## Prerequisites

- Docker Desktop (with Compose v2 — `docker compose`, not `docker-compose`)
- An API key for whichever LLM provider you'll use (or none, for local
  Ollama) — see [Configuring the AI provider](#configuring-the-ai-provider)

## Setup

```bash
git clone <this-repo>
cd talentlens-ai
cp .env.example .env
```

Open `.env` and set at minimum:
- `JWT_SECRET` — any long random string for local dev
  (`python3 -c "import secrets; print(secrets.token_urlsafe(48))"`)
- `LLM_PROVIDER` + the matching API key (see below)

```bash
make up
# equivalent to: docker compose -f infra/docker-compose.yml up --build
```

This brings up Postgres+pgvector, Redis, MinIO, the FastAPI backend, the
Celery worker, and the Next.js frontend. The backend container runs
`alembic upgrade head` automatically before starting, so the schema is
always current on boot — no manual migration step needed for a fresh
clone.

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| MinIO console | http://localhost:9001 (user/pass: `talentlens` / `talentlens123`) |

### First login

There's no seeded demo account. Go to http://localhost:3000/login, switch
to **Register**, and create an organization + admin user — that single call
(`POST /auth/register`) creates both.

### Configuring the AI provider

Set `LLM_PROVIDER` in `.env` to one of:

- **`ollama`** (default) — fully local/offline, no API key. Requires a
  running Ollama server (`OLLAMA_BASE_URL`, default
  `http://localhost:11434`) with `OLLAMA_MODEL`/`OLLAMA_EMBEDDING_MODEL`
  pulled.
- **`groq`** — fast, cheap hosted inference. Set `GROQ_API_KEY` and
  `GROQ_MODEL` (check [console.groq.com/docs/models](https://console.groq.com/docs/models) —
  Groq periodically decommissions older models). **Groq has no embeddings
  API** — semantic scoring degrades gracefully to a neutral score with
  this provider alone. See `docs/design-decisions.md` for the tradeoff.
- **`openai`** — set `OPENAI_API_KEY`; supports both chat and embeddings.

If the configured provider is unreachable or misconfigured, the app keeps
working — resume text/keyword search still function, structured
extraction/semantic scoring/AI narrative just degrade to their
deterministic fallbacks rather than failing the request. See
[`docs/architecture.md#graceful-degradation`](docs/architecture.md).

## Running things day-to-day

```bash
make up             # start the full stack (rebuilds if code changed)
make down            # stop it
make logs             # tail all container logs
make migrate          # apply pending Alembic migrations manually
make migration msg="add foo column"   # generate a new migration
make test             # run backend pytest suite
make lint              # ruff (backend) + next lint (frontend)
make backend-shell      # shell into the backend container
make db-shell            # psql into the database
make clean                # docker compose down -v (drops volumes/data)
```

**Backend hot-reloads** on file changes (bind-mounted, `uvicorn --reload`).
**Frontend does not** — it's a production `next build` inside the
container with no bind mount. After changing frontend code:
```bash
docker compose -f infra/docker-compose.yml up -d --build frontend
```

### Running the frontend or backend outside Docker

```bash
# backend
cd backend
python -m venv venv && source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# (needs Postgres/Redis/MinIO reachable at the *_URL vars in .env — either
# run those three via `docker compose up postgres redis minio`, or point
# the URLs at your own instances)

# frontend
cd frontend
npm install
npm run dev
```

### Tests

```bash
make test
# or, inside backend/: pytest tests/ -v
```
Unit tests cover the deterministic matching engines (skill/education/
experience/scoring), extraction schema validation, and ingestion
(PDF/DOCX text extraction, cleaning). LLM calls are mocked
(`backend/tests/fixtures/mock_llm.py`) — no live API key needed to run
the suite.

## Documentation

| Doc | Covers |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | Component diagram, request-flow sequence diagrams, multi-tenancy, graceful degradation, the event-loop-per-Celery-task constraint |
| [`docs/database.md`](docs/database.md) | Every table/column, ER diagram, indexes, migration history, how to regenerate the schema dump |
| [`docs/api.md`](docs/api.md) | How to use the Swagger/ReDoc/Postman docs, auth flow, endpoint groups |
| [`docs/api/openapi.json`](docs/api/openapi.json), [`docs/api/postman_collection.json`](docs/api/postman_collection.json) | Machine-readable API spec + importable Postman collection |
| [`docs/design-decisions.md`](docs/design-decisions.md) | Why matching is on-demand not automatic, why scoring is deterministic with LLM-only narrative, tenant-isolation approach, UI design system, explicit assumptions |

## Known gaps

Tracked here rather than in a stale progress log — check the code before
trusting this list, it will drift:

- **Blind screening** (hiding candidate name/demographics from the initial
  recruiter view) is not implemented.
- **API rate limiting** is not implemented at the application layer.
- **Semantic scoring requires an embeddings-capable provider** (`openai` or
  `ollama`) — see [Configuring the AI provider](#configuring-the-ai-provider).
- **No fuzzy candidate-identity resolution** — two resumes for the same
  person (different file, same content) create two candidate records
  unless the file is byte-identical. See `docs/design-decisions.md`.
- Some extracted resume text contains encoding artifacts (mojibake, e.g.
  `â€™` instead of `'`) from certain source PDFs — likely in the PyMuPDF
  text-extraction or cleaning step (`app/ingestion/pdf_parser.py` /
  `text_cleaner.py`); not yet root-caused.
