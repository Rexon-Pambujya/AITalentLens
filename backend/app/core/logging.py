"""
Structured (JSON-capable) logging with request-scoped context.

Every log line emitted during a request automatically carries request_id /
user_id / organization_id once bound via `bind_request_context`, satisfying
the observability requirements (section 40): every request should be
traceable by request_id, user_id, organization_id, endpoint, latency, status.
"""
import logging
import sys
import time
import uuid
from contextvars import ContextVar

import structlog

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")
user_id_ctx: ContextVar[str] = ContextVar("user_id", default="-")
organization_id_ctx: ContextVar[str] = ContextVar("organization_id", default="-")


def _inject_context(logger, method_name, event_dict):
    event_dict["request_id"] = request_id_ctx.get()
    event_dict["user_id"] = user_id_ctx.get()
    event_dict["organization_id"] = organization_id_ctx.get()
    return event_dict


def configure_logging(json_logs: bool = True) -> None:
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO)

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        _inject_context,
    ]

    structlog.configure(
        processors=shared_processors
        + [
            structlog.processors.JSONRenderer()
            if json_logs
            else structlog.dev.ConsoleRenderer()
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "talentlens"):
    return structlog.get_logger(name)


def new_request_id() -> str:
    return str(uuid.uuid4())


class Timer:
    """Small helper for consistent latency measurement around a stage.

    Usage:
        with Timer() as t:
            do_work()
        logger.info("stage_complete", stage="embedding", duration_ms=t.duration_ms)
    """

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *exc):
        self.duration_ms = round((time.perf_counter() - self._start) * 1000, 2)
