"""
Education matching (section 14).

Handles degree-name variance ("B.Tech Computer Science" / "B.E. Information
Technology" / "M.Sc Computer Science") via a normalized degree-level
hierarchy rather than exact string matching, so equivalent degrees aren't
incorrectly rejected.
"""
from dataclasses import dataclass
from enum import IntEnum


class DegreeLevel(IntEnum):
    NONE = 0
    ASSOCIATE = 1
    BACHELORS = 2
    MASTERS = 3
    DOCTORATE = 4


_DEGREE_PATTERNS: list[tuple[str, DegreeLevel]] = [
    ("phd", DegreeLevel.DOCTORATE), ("ph.d", DegreeLevel.DOCTORATE), ("doctorate", DegreeLevel.DOCTORATE),
    ("m.sc", DegreeLevel.MASTERS), ("msc", DegreeLevel.MASTERS), ("m.s.", DegreeLevel.MASTERS),
    ("master", DegreeLevel.MASTERS), ("mba", DegreeLevel.MASTERS), ("m.tech", DegreeLevel.MASTERS),
    ("mtech", DegreeLevel.MASTERS), ("meng", DegreeLevel.MASTERS), ("m.eng", DegreeLevel.MASTERS),
    ("b.tech", DegreeLevel.BACHELORS), ("btech", DegreeLevel.BACHELORS), ("b.e.", DegreeLevel.BACHELORS),
    ("be ", DegreeLevel.BACHELORS), ("b.s.", DegreeLevel.BACHELORS), ("bs ", DegreeLevel.BACHELORS),
    ("bachelor", DegreeLevel.BACHELORS), ("b.a.", DegreeLevel.BACHELORS), ("ba ", DegreeLevel.BACHELORS),
    ("associate", DegreeLevel.ASSOCIATE),
]

# Field synonyms so "Information Technology" and "Computer Science" can be
# treated as related-enough for most engineering roles without being
# identical. Kept intentionally small and explicit.
_FIELD_GROUPS: list[set[str]] = [
    {"computer science", "software engineering", "information technology", "computer engineering", "cs"},
    {"data science", "statistics", "applied mathematics", "mathematics"},
    {"electrical engineering", "electronics engineering", "computer engineering"},
]


@dataclass
class EducationMatchResult:
    highest_candidate_level: DegreeLevel
    required_level: DegreeLevel
    meets_level_requirement: bool
    field_match: bool | None  # None if no field was required
    score: float  # 0-100


def parse_degree_level(degree_text: str | None) -> DegreeLevel:
    if not degree_text:
        return DegreeLevel.NONE
    lowered = degree_text.lower()
    for pattern, level in _DEGREE_PATTERNS:
        if pattern in lowered:
            return level
    return DegreeLevel.NONE


def _fields_related(a: str | None, b: str | None) -> bool:
    if not a or not b:
        return False
    a_l, b_l = a.lower().strip(), b.lower().strip()
    if a_l == b_l:
        return True
    return any(a_l in group and b_l in group for group in _FIELD_GROUPS)


def match_education(
    *,
    candidate_degrees: list[tuple[str | None, str | None]],
    required_level: DegreeLevel,
    required_field: str | None,
) -> EducationMatchResult:
    """Pure function - fully unit-testable."""
    if not candidate_degrees:
        highest = DegreeLevel.NONE
    else:
        parsed = [(parse_degree_level(d), f) for d, f in candidate_degrees]
        highest = max(level for level, _ in parsed)

    meets_level = highest >= required_level

    # A candidate with NO parseable degree at all can't have a "field
    # match" either - there's nothing to match a field against. Handle
    # this as a distinct, low-scoring case up front rather than letting a
    # "no field required" default (which legitimately means 100%) leak in
    # and prop up a candidate who has no degree whatsoever.
    if highest == DegreeLevel.NONE:
        best_field_match = None if required_field is None else False
        score = 100.0 if required_level == DegreeLevel.NONE else 0.0
        return EducationMatchResult(
            highest_candidate_level=highest,
            required_level=required_level,
            meets_level_requirement=meets_level,
            field_match=best_field_match,
            score=score,
        )

    if required_field is None:
        best_field_match = None
    else:
        best_field_match = any(_fields_related(f, required_field) for _, f in parsed)

    if required_level == DegreeLevel.NONE or meets_level:
        level_score = 100.0
    else:
        gap = required_level - highest
        level_score = max(0.0, 100.0 - gap * 40.0)

    if best_field_match is None:
        field_component = 100.0
    else:
        field_component = 100.0 if best_field_match else 60.0

    score = round(level_score * 0.7 + field_component * 0.3, 1)

    return EducationMatchResult(
        highest_candidate_level=highest,
        required_level=required_level,
        meets_level_requirement=meets_level,
        field_match=best_field_match,
        score=score,
    )


def education_score(result: EducationMatchResult) -> float:
    return result.score
