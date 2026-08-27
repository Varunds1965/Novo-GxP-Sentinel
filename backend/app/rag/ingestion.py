"""The twelve-step ingestion pipeline.

Order is fixed and no step is skippable by configuration (SEC-R-014). Nothing
uploaded is ever TRUSTED on arrival (SEC-R-015).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath, PureWindowsPath

from app.domain.clock import ClockPort
from app.domain.enums import ApprovalStatus, TrustLevel
from app.domain.errors import (
    ExtractionError,
    FileTooLargeError,
    UnsupportedFormatError,
    ValidationError,
)
from app.domain.hashing import sha256_bytes
from app.domain.models import SourceRecord
from app.security.injection import ScanResult, scan

MAX_UPLOAD_BYTES = 12 * 1024 * 1024  # 12 MB ceiling from the Visual User Manual
ALLOWED_EXTENSIONS = frozenset({"md", "txt", "csv", "json", "pdf", "docx", "xlsx"})

_MAGIC: dict[str, tuple[bytes, ...]] = {
    "pdf": (b"%PDF-",),
    "docx": (b"PK\x03\x04",),
    "xlsx": (b"PK\x03\x04",),
}

_RESERVED_WINDOWS = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

_CHUNK_TARGET_CHARS = 1400
_CHUNK_OVERLAP_CHARS = 160


@dataclass(frozen=True, slots=True)
class Chunk:
    chunk_id: str
    source_id: str
    ordinal: int
    location: str
    text: str


@dataclass(frozen=True, slots=True)
class IngestionOutcome:
    record: SourceRecord
    chunks: tuple[Chunk, ...]
    scan_result: ScanResult
    duplicate_of: str | None = None

    @property
    def indexed(self) -> bool:
        """Quarantined content is never indexed (SEC-R-016)."""
        return not self.record.is_quarantined and self.duplicate_of is None


def safe_filename(raw: str) -> str:
    """Uploaded filenames are never trusted (FOLD-R-010)."""
    if not raw or raw.strip() in {".", ".."}:
        raise ValidationError(
            "That file has no usable name.", remediation="Rename the file and try again."
        )
    if "\x00" in raw:
        raise ValidationError("That filename contains an illegal character.")
    # Reduce-to-basename would already be safe, but an explicit refusal means the
    # attempt is recorded in the audit trail instead of silently normalised away.
    if ".." in raw.replace("\\", "/").split("/") or raw.startswith(("/", "\\\\")):
        raise ValidationError(
            "That filename looks like a path rather than a file name.",
            remediation="Rename the file so it contains no folder separators.",
        )
    name = PurePosixPath(PureWindowsPath(raw).name).name
    if name in {"", ".", ".."} or name.startswith("~"):
        raise ValidationError("That filename is not permitted.")
    stem = name.rsplit(".", 1)[0].upper()
    if stem in _RESERVED_WINDOWS:
        raise ValidationError(f"{stem} is a reserved device name on Windows.")
    return name


def extension_of(filename: str) -> str:
    if "." not in filename:
        raise UnsupportedFormatError(
            "That file has no extension.",
            remediation="Use MD, TXT, CSV, JSON, PDF, DOCX or XLSX, up to 12 MB.",
        )
    return filename.rsplit(".", 1)[1].lower()


def validate_extension(filename: str) -> str:
    ext = extension_of(filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise UnsupportedFormatError(
            "That file type is not supported.",
            remediation="Use MD, TXT, CSV, JSON, PDF, DOCX or XLSX, up to 12 MB.",
        )
    return ext


def validate_size(payload: bytes) -> int:
    """Enforced by real byte count, never a client-supplied Content-Length."""
    size = len(payload)
    if size == 0:
        raise ValidationError("That file is empty.", remediation="Choose a file with content.")
    if size > MAX_UPLOAD_BYTES:
        raise FileTooLargeError(
            f"That file is {size / 1_048_576:.1f} MB, which exceeds the 12 MB limit.",
            remediation="Upload a smaller extract of the document.",
        )
    return size


def sniff_magic(payload: bytes, ext: str) -> None:
    """A .pdf that is actually a ZIP is rejected (SEC-R-014 step 3)."""
    expected = _MAGIC.get(ext)
    if expected and not any(payload.startswith(sig) for sig in expected):
        raise UnsupportedFormatError(
            f"That file claims to be {ext.upper()} but its content does not match.",
            remediation="Re-export the document and try again.",
        )


def chunk_text(source_id: str, text: str) -> tuple[Chunk, ...]:
    """Deterministic boundaries and stable chunk IDs."""
    normalised = re.sub(r"\n{3,}", "\n\n", text.replace("\r\n", "\n")).strip()
    if not normalised:
        return ()
    chunks: list[Chunk] = []
    cursor = 0
    ordinal = 0
    while cursor < len(normalised):
        end = min(len(normalised), cursor + _CHUNK_TARGET_CHARS)
        if end < len(normalised):
            window = normalised.rfind("\n", cursor + _CHUNK_TARGET_CHARS // 2, end)
            if window == -1:
                window = normalised.rfind(". ", cursor + _CHUNK_TARGET_CHARS // 2, end)
            if window != -1:
                end = window + 1
        body = normalised[cursor:end].strip()
        if body:
            chunks.append(
                Chunk(
                    chunk_id=f"{source_id}#c{ordinal:04d}",
                    source_id=source_id,
                    ordinal=ordinal,
                    location=f"chars {cursor}-{end}",
                    text=body,
                )
            )
            ordinal += 1
        if end <= cursor:
            break
        cursor = max(end - _CHUNK_OVERLAP_CHARS, end) if end < len(normalised) else end
    return tuple(chunks)


class IngestionPipeline:
    def __init__(
        self,
        clock: ClockPort,
        extractors: dict[str, "object"],
        known_hashes: dict[str, str] | None = None,
    ) -> None:
        self._clock = clock
        self._extractors = extractors
        self._known_hashes = known_hashes if known_hashes is not None else {}

    def ingest(
        self,
        *,
        filename: str,
        payload: bytes,
        system_id: str,
        uploaded_by: str,
        document_type: str = "UPLOADED_EVIDENCE",
        source_system: str = "LOCAL_UPLOAD",
    ) -> IngestionOutcome:
        name = safe_filename(filename)                        # 1 name hygiene
        ext = validate_extension(name)                        # 1 extension allowlist
        size = validate_size(payload)                         # 2 size ceiling
        sniff_magic(payload, ext)                             # 3 magic-byte sniff
        digest = sha256_bytes(payload)                        # 4 hash raw bytes first
        duplicate = self._known_hashes.get(digest)            # 5 duplicate detection

        extractor = self._extractors.get(ext)
        if extractor is None:
            raise UnsupportedFormatError(f"No extractor is registered for {ext.upper()}.")
        extracted = extractor.extract(payload)                # 6 bounded extraction
        if not extracted.text.strip():
            raise ExtractionError(
                "No text could be extracted.",
                remediation=(
                    "This looks like a scanned image file, and OCR is outside the "
                    "scope of this prototype. Upload a text-based version, or "
                    "record the evidence manually."
                ),
            )

        scan_result = scan(extracted.text, source_hint=name)  # 7 injection scan
        trust = (                                             # 8 trust assignment
            TrustLevel.QUARANTINED_UNTRUSTED
            if scan_result.is_suspicious
            else TrustLevel.UNTRUSTED_REVIEW_REQUIRED
        )

        source_id = f"UPL-{digest[:12].upper()}"
        record = SourceRecord(                                # 11 provenance
            source_id=source_id,
            title=name,
            document_type=document_type,
            system_id=system_id,
            version="uploaded",
            approval_status=ApprovalStatus.UNKNOWN,
            trust_level=trust,
            content_hash=digest,
            source_system=source_system,
            ingested_at=self._clock.now(),
            owner=uploaded_by,
            byte_size=size,
            page_count=extracted.page_count,
            injection_findings=scan_result.categories,
        )
        chunks = () if trust is TrustLevel.QUARANTINED_UNTRUSTED else chunk_text(source_id, extracted.text)
        if duplicate is None:
            self._known_hashes[digest] = source_id
        return IngestionOutcome(
            record=record, chunks=chunks, scan_result=scan_result, duplicate_of=duplicate
        )
