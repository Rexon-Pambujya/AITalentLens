"""
Application entrypoint. Run locally with:

    uvicorn app.main:app --reload --port 8000

Or via Docker Compose (see infra/docker-compose.yml), which is the intended
way to run the full stack (Postgres+pgvector, Redis, Celery worker, MinIO).
"""
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import (
    configure_logging,
    get_logger,
    new_request_id,
    organization_id_ctx,
    request_id_ctx,
    user_id_ctx,
)

settings = get_settings()
configure_logging(json_logs=settings.ENVIRONMENT != "local")
logger = get_logger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="AI-powered candidate intelligence for faster, fairer hiring.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        """Binds request_id (and user/org, once auth runs) for structured
        logging + timing, satisfying spec section 40 (Observability)."""
        req_id = request.headers.get("X-Request-ID", new_request_id())
        token_req = request_id_ctx.set(req_id)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            request_id_ctx.reset(token_req)
            raise
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-ID"] = req_id
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        request_id_ctx.reset(token_req)
        return response

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/", tags=["root"])
    async def root():
        return {
            "product": settings.PROJECT_NAME,
            "tagline": "AI-powered candidate intelligence for faster, fairer hiring.",
            "docs": "/docs",
        }

    return app


app = create_app()
