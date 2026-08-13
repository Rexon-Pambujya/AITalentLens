#!/usr/bin/env python3
"""
Regenerates docs/api/postman_collection.json from docs/api/openapi.json.

Run whenever the API surface changes:
    1. Regenerate openapi.json (from a Python that has the backend deps
       installed - either the container or backend/venv):
         python -c "
import json, os
os.environ.setdefault('JWT_SECRET','local')
os.environ.setdefault('DATABASE_URL','postgresql+asyncpg://x:x@localhost/x')
os.environ.setdefault('DATABASE_URL_SYNC','postgresql+psycopg2://x:x@localhost/x')
os.environ.setdefault('REDIS_URL','redis://localhost:6379/0')
os.environ.setdefault('CELERY_BROKER_URL','redis://localhost:6379/1')
os.environ.setdefault('CELERY_RESULT_BACKEND','redis://localhost:6379/2')
from app.main import app
json.dump(app.openapi(), open('docs/api/openapi.json', 'w'), indent=2)
"
       ...or simply: curl http://localhost:8000/openapi.json -o docs/api/openapi.json
    2. python docs/api/generate_postman.py
"""
import json
import re
import uuid
from pathlib import Path

HERE = Path(__file__).parent
SPEC = json.loads((HERE / "openapi.json").read_text())

_PLACEHOLDER_BY_FORMAT = {
    "date": "2026-01-01",
    "date-time": "2026-01-01T00:00:00Z",
    "uuid": "00000000-0000-0000-0000-000000000000",
    "email": "user@example.com",
}


def resolve_ref(ref: str) -> dict:
    # Only local #/components/schemas/... refs are used in this spec.
    _, _, path = ref.partition("#/")
    node = SPEC
    for part in path.split("/"):
        node = node[part]
    return node


def example_for_schema(schema: dict, seen: frozenset = frozenset()) -> object:
    if "$ref" in schema:
        ref = schema["$ref"]
        if ref in seen:
            return None  # cycle guard
        return example_for_schema(resolve_ref(ref), seen | {ref})

    if "example" in schema:
        return schema["example"]
    if "default" in schema:
        return schema["default"]
    if "enum" in schema:
        return schema["enum"][0]

    # anyOf/oneOf (commonly `T | None` in the FastAPI-generated spec) - use
    # the first non-null branch.
    for key in ("anyOf", "oneOf"):
        if key in schema:
            for branch in schema[key]:
                if branch.get("type") != "null":
                    return example_for_schema(branch, seen)
            return None

    schema_type = schema.get("type")
    fmt = schema.get("format")

    if schema_type == "object" or "properties" in schema:
        return {
            name: example_for_schema(prop, seen)
            for name, prop in schema.get("properties", {}).items()
        }
    if schema_type == "array":
        item_schema = schema.get("items", {})
        return [example_for_schema(item_schema, seen)]
    if schema_type == "string":
        if fmt in _PLACEHOLDER_BY_FORMAT:
            return _PLACEHOLDER_BY_FORMAT[fmt]
        return schema.get("title", "string")
    if schema_type == "integer":
        return 0
    if schema_type == "number":
        return 0.0
    if schema_type == "boolean":
        return True
    return None


def path_to_postman(path: str) -> str:
    """/jobs/{job_id} -> /jobs/:job_id (Postman path-variable syntax)."""
    return re.sub(r"\{(\w+)\}", r":\1", path)


def path_variables(path: str) -> list[dict]:
    return [
        {"key": name, "value": "REPLACE_ME"}
        for name in re.findall(r"\{(\w+)\}", path)
    ]


def build_request(method: str, path: str, op: dict) -> dict:
    item = {
        "name": op.get("summary") or f"{method.upper()} {path}",
        "request": {
            "method": method.upper(),
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "url": {
                "raw": "{{base_url}}" + path_to_postman(path),
                "host": ["{{base_url}}"],
                "path": [p for p in path_to_postman(path).split("/") if p],
                "variable": path_variables(path),
            },
        },
        "response": [],
    }

    body_spec = (
        op.get("requestBody", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema")
    )
    if body_spec:
        example = example_for_schema(body_spec)
        item["request"]["body"] = {
            "mode": "raw",
            "raw": json.dumps(example, indent=2),
            "options": {"raw": {"language": "json"}},
        }

    # auth/register and auth/login don't need a bearer token yet.
    if path in ("/api/v1/auth/register", "/api/v1/auth/login"):
        item["request"]["auth"] = {"type": "noauth"}

    return item


def main() -> None:
    folders: dict[str, list[dict]] = {}
    for path, methods in SPEC["paths"].items():
        for method, op in methods.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue
            tag = (op.get("tags") or ["misc"])[0]
            folders.setdefault(tag, []).append(build_request(method, path, op))

    collection = {
        "info": {
            "_postman_id": str(uuid.uuid4()),
            "name": SPEC["info"]["title"],
            "description": SPEC["info"].get("description", ""),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "auth": {
            "type": "bearer",
            "bearer": [{"key": "token", "value": "{{token}}", "type": "string"}],
        },
        "variable": [
            {"key": "base_url", "value": "http://localhost:8000/api/v1"},
            {"key": "token", "value": ""},
        ],
        "item": [
            {"name": tag, "item": items} for tag, items in sorted(folders.items())
        ],
    }

    out = HERE / "postman_collection.json"
    out.write_text(json.dumps(collection, indent=2))
    print(f"Wrote {out} ({sum(len(v) for v in folders.values())} requests)")


if __name__ == "__main__":
    main()
