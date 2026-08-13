"""
Lightweight, dependency-free normalization helpers.

`normalize_skill_name` is intentionally simple (lowercase + strip + known
alias table) for this phase. The full skill taxonomy will live in the
`skills` table (see app/models/skill.py) and be looked up/extended by
`matching/skill_matcher.py` in a later phase; this function is the fallback
normalizer used before a skill has a canonical taxonomy row.
"""
import re

# A small seed of common aliases -> canonical form. This is deliberately
# not exhaustive; the DB-backed taxonomy takes precedence once populated.
_SKILL_ALIASES: dict[str, str] = {
    "pytorch": "PyTorch",
    "torch": "PyTorch",
    "tensorflow": "TensorFlow",
    "tf": "TensorFlow",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "psql": "PostgreSQL",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "aws": "AWS",
    "amazon web services": "AWS",
    "gcp": "GCP",
    "google cloud": "GCP",
    "google cloud platform": "GCP",
    "langchain": "LangChain",
    "langgraph": "LangGraph",
    "nlp": "Natural Language Processing",
    "cv": "Computer Vision",
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",
    "genai": "Generative AI",
    "generative ai": "Generative AI",
}


def normalize_text(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"\s+", " ", value)
    return value


def normalize_skill_name(raw_skill: str) -> str:
    """Returns the canonical display form of a skill string.

    >>> normalize_skill_name("pytorch")
    'PyTorch'
    >>> normalize_skill_name("  Kubernetes ")
    'Kubernetes'
    >>> normalize_skill_name("Snowflake")
    'Snowflake'
    """
    key = normalize_text(raw_skill)
    key = key.strip(".,;:()[]")
    if key in _SKILL_ALIASES:
        return _SKILL_ALIASES[key]
    # No known alias - title-case single words, leave multi-word/acronym-ish
    # strings as originally provided (trimmed) to avoid mangling things like
    # "FastAPI" or "gRPC".
    stripped = raw_skill.strip()
    if stripped.isupper() and len(stripped) <= 5:
        return stripped  # likely an acronym e.g. "AWS", "SQL"
    return stripped
