"""Extractor port and the zero-dependency text formats."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from typing import Protocol

from app.domain.errors import ExtractionError

MAX_EXTRACTED_CHARS = 4_000_000


@dataclass(frozen=True, slots=True)
class Extracted:
    text: str
    page_count: int = 1
    notes: tuple[str, ...] = ()


class ExtractorPort(Protocol):
    extension: str

    def extract(self, payload: bytes) -> Extracted: ...


def _decode(payload: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return payload.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ExtractionError("That file's text encoding could not be read.")


def _cap(text: str) -> str:
    return text[:MAX_EXTRACTED_CHARS]


class TextExtractor:
    extension = "txt"

    def extract(self, payload: bytes) -> Extracted:
        return Extracted(text=_cap(_decode(payload)))


class MarkdownExtractor(TextExtractor):
    extension = "md"


class JsonExtractor:
    extension = "json"

    def extract(self, payload: bytes) -> Extracted:
        raw = _decode(payload)
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ExtractionError(
                "That JSON file could not be parsed.",
                remediation="Check the file for a syntax error and re-export it.",
            ) from exc
        return Extracted(text=_cap(json.dumps(parsed, indent=2, ensure_ascii=False)))


class CsvExtractor:
    extension = "csv"

    def extract(self, payload: bytes) -> Extracted:
        raw = _decode(payload)
        reader = csv.reader(io.StringIO(raw))
        lines = [" | ".join(cell.strip() for cell in row) for row in reader if any(row)]
        if not lines:
            raise ExtractionError("That CSV file contained no rows.")
        return Extracted(text=_cap("\n".join(lines)))
