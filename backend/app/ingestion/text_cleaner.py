"""
Text cleaning + section-aware chunking.

Chunking matters a lot for match quality (section 12: "Do not rely solely
on one whole-resume embedding. Use chunk-level embeddings.") - a resume
embedded as one 2-page blob dilutes the specific sentence that proves a
skill. We chunk by detected section, then by paragraph within an
oversized section, so each embedding stays semantically coherent.
"""
import re

# Common resume section headers - matched case-insensitively at the start
# of a line. Not exhaustive; unmatched text falls into a "general" bucket
# rather than being dropped.
_SECTION_HEADERS = [
    "summary", "objective", "profile",
    "experience", "work experience", "employment history", "professional experience",
    "education",
    "skills", "technical skills", "core competencies",
    "projects",
    "certifications", "licenses",
    "publications", "awards", "achievements",
    "languages",
]

_HEADER_PATTERN = re.compile(
    r"^\s*(" + "|".join(re.escape(h) for h in _SECTION_HEADERS) + r")\s*:?\s*$",
    re.IGNORECASE,
)

MAX_CHUNK_CHARS = 1200


def clean_text(raw_text: str) -> str:
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def detect_sections(cleaned_text: str) -> dict[str, str]:
    """Splits cleaned resume text into {section_name: section_text}. Text
    before the first recognized header is bucketed under 'general' (this is
    typically the contact-info / name block)."""
    lines = cleaned_text.split("\n")
    sections: dict[str, list[str]] = {"general": []}
    current = "general"

    for line in lines:
        match = _HEADER_PATTERN.match(line.strip())
        if match:
            current = match.group(1).lower()
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)

    return {name: "\n".join(lines_).strip() for name, lines_ in sections.items() if "\n".join(lines_).strip()}


def chunk_text_for_embedding(cleaned_text: str) -> list[str]:
    """Returns a list of chunk strings, section-aware and length-capped.
    Order is preserved so `chunk_index` is stable and meaningful."""
    sections = detect_sections(cleaned_text)
    chunks: list[str] = []

    for section_name, section_text in sections.items():
        if len(section_text) <= MAX_CHUNK_CHARS:
            chunks.append(f"[{section_name}]\n{section_text}")
            continue
        # Oversized section (usually "experience") - split on blank lines
        # (paragraph boundaries) and greedily pack up to MAX_CHUNK_CHARS.
        paragraphs = [p.strip() for p in section_text.split("\n\n") if p.strip()]
        buffer = ""
        for para in paragraphs:
            candidate = f"{buffer}\n\n{para}".strip() if buffer else para
            if len(candidate) > MAX_CHUNK_CHARS and buffer:
                chunks.append(f"[{section_name}]\n{buffer}")
                buffer = para
            else:
                buffer = candidate
        if buffer:
            chunks.append(f"[{section_name}]\n{buffer}")

    return chunks if chunks else [cleaned_text[:MAX_CHUNK_CHARS]]
