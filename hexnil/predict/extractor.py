"""Claim ingestion and deterministic extraction layer for Phase 7."""

import re
from typing import List, Optional
from hexnil.predict.models import ExtractionMethod, RawClaim

PARSER_VERSION = "1.0.0"

# Regular expression to detect and strip leading bullet/list markers
_BULLET_REGEX = re.compile(
    r"^\s*(?:[-*+•–—]|\d+[.)]|\([0-9a-zA-Z]+\))\s+",
    re.UNICODE,
)


def ingest_raw_text(text: str, source: str = "release_notes") -> List[RawClaim]:
    """Ingest raw release notes and split into candidate claim chunks while preserving original text.

    Handles:
    - Bullet points (-, *, +, numbers, etc.)
    - Paragraphs and multi-line text
    - Semicolon-separated lists if on individual lines
    """
    if not text or not text.strip():
        return []

    raw_claims: List[RawClaim] = []
    lines = text.splitlines()

    current_chunk: List[str] = []
    current_line_num: Optional[int] = None

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            if current_chunk:
                combined_raw = "\n".join(current_chunk)
                raw_claims.append(
                    RawClaim(
                        raw_text=combined_raw,
                        line_number=current_line_num,
                        source=source,
                    )
                )
                current_chunk = []
                current_line_num = None
            continue

        is_bullet = bool(_BULLET_REGEX.match(line))

        if is_bullet:
            if current_chunk:
                combined_raw = "\n".join(current_chunk)
                raw_claims.append(
                    RawClaim(
                        raw_text=combined_raw,
                        line_number=current_line_num,
                        source=source,
                    )
                )
                current_chunk = []

            current_chunk.append(line)
            current_line_num = idx
        else:
            if not current_chunk:
                current_line_num = idx
            current_chunk.append(line)

    if current_chunk:
        combined_raw = "\n".join(current_chunk)
        raw_claims.append(
            RawClaim(
                raw_text=combined_raw,
                line_number=current_line_num,
                source=source,
            )
        )

    return raw_claims


def normalize_claim_text(raw_text: str) -> str:
    """Produce clean, normalized representation of raw claim text.

    - Strips leading bullet markers and whitespace
    - Normalizes internal whitespace to single spaces
    - Preserves semantic casing while providing clean string
    """
    if not raw_text:
        return ""

    # Replace newlines inside multi-line bullet with space
    text = " ".join(raw_text.splitlines())

    # Strip bullet prefix
    text = _BULLET_REGEX.sub("", text)

    # Collapse repeated whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text
