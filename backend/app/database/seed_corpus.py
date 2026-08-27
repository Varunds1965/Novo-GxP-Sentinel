"""Deterministic ingestion of the MES PAS-X evidence package.

The corpus is the mentor-supplied NOVOLIFE MES PAS-X lifecycle package: 35
DUMMY documents that cross-reference 50 requirements, 26 shared risks, 50
configuration items and 6 validation deviations. Nothing here is invented; the
document type, title and identifier are parsed from the supplied filenames and
control blocks.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.domain.clock import ClockPort
from app.domain.enums import ApprovalStatus, FindingCategory, TrustLevel
from app.domain.models import ChecklistQuestion, SourceRecord
from app.rag.extractors.office import default_extractors
from app.rag.ingestion import IngestionPipeline

SYSTEM_ID = "NL-MES-001"
SYSTEM_NAME = "MES PAS-X (Novo Life, synthetic)"

_FILENAME = re.compile(r"^NOVOLIFE-MES-([A-Z]{2,6})-(.+?)-v([\d.]+)-DUMMY\.docx$")

# Documents that carry a real document date in their control block.
_DATED = {
    "AMRR": "2026-08-12", "ATR": "2026-08-12", "CHG": "2026-08-12",
    "INC": "2026-08-12", "ITPSE": "2026-08-12", "TRN": "2026-08-12",
    "URR": "2026-08-12", "VSR": "2026-08-12", "IQP": "2026-08-11",
    "TRM": "2026-08-11",
}


@dataclass(frozen=True, slots=True)
class SeedResult:
    sources: tuple[SourceRecord, ...]
    chunks_indexed: int
    quarantined: tuple[str, ...]


def _approval_status(text: str) -> ApprovalStatus:
    """A training banner that says 'approved' is not an approval.

    Every document in this package is v0.1 and states that it is not valid for
    operational, regulatory, inspection or GxP release use. Several also carry
    the phrase 'Simulated Reviewed and Approved for Demo/Training Use Only'.
    Treating that phrase as an approved status is exactly the authority bias the
    master SOP requires us to defeat, so it is recorded as DRAFT.
    """
    lowered = text[:4000].lower()
    if "simulated" in lowered or "dummy" in lowered or "not valid for" in lowered:
        return ApprovalStatus.DRAFT
    if re.search(r"\bstatus\b\s*\|\s*approved\b", lowered):
        return ApprovalStatus.APPROVED
    return ApprovalStatus.DRAFT


def seed_corpus(
    corpus_dir: Path,
    retrieval,
    clock: ClockPort,
    *,
    system_id: str = SYSTEM_ID,
) -> SeedResult:
    pipeline = IngestionPipeline(clock, default_extractors())
    sources: list[SourceRecord] = []
    quarantined: list[str] = []
    indexed = 0

    for path in sorted(corpus_dir.glob("*.docx")):
        match = _FILENAME.match(path.name)
        doc_type = match.group(1) if match else "UNKNOWN"
        title = match.group(2).replace("-", " ") if match else path.stem
        version = match.group(3) if match else "0.1"

        outcome = pipeline.ingest(
            filename=path.name,
            payload=path.read_bytes(),
            system_id=system_id,
            uploaded_by="corpus-seed",
            document_type=doc_type,
            source_system="MENTOR_EVIDENCE_PACKAGE",
        )
        body = "\n".join(c.text for c in outcome.chunks[:4])
        effective = (
            datetime.fromisoformat(_DATED[doc_type]).replace(tzinfo=UTC)
            if doc_type in _DATED
            else None
        )
        record = SourceRecord(
            source_id=f"NL-MES-{doc_type}-001",
            title=title,
            document_type=doc_type,
            system_id=system_id,
            version=version,
            approval_status=_approval_status(body),
            trust_level=outcome.record.trust_level,
            content_hash=outcome.record.content_hash,
            source_system="MENTOR_EVIDENCE_PACKAGE",
            ingested_at=outcome.record.ingested_at,
            effective_date=effective,
            review_date=None,
            owner="Novo Life (synthetic)",
            byte_size=outcome.record.byte_size,
            page_count=outcome.record.page_count,
            injection_findings=outcome.record.injection_findings,
        )
        sources.append(record)
        if record.is_quarantined:
            quarantined.append(record.source_id)
            continue
        renamed = tuple(
            type(c)(
                chunk_id=c.chunk_id.replace(outcome.record.source_id, record.source_id),
                source_id=record.source_id,
                ordinal=c.ordinal,
                location=c.location,
                text=c.text,
            )
            for c in outcome.chunks
        )
        indexed += retrieval.index_chunks(renamed)

    return SeedResult(
        sources=tuple(sources), chunks_indexed=indexed, quarantined=tuple(quarantined)
    )


def load_checklists(path: Path) -> tuple[ChecklistQuestion, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    questions: list[ChecklistQuestion] = []
    for raw in payload["questions"]:
        questions.append(
            ChecklistQuestion(
                q_id=raw["q_id"],
                phase_no=raw["phase_no"],
                lifecycle_phase=raw["lifecycle_phase"],
                sequence=raw["sequence"],
                audit_domain=raw["audit_domain"],
                control_topic=raw["control_topic"],
                applies_to=raw["applies_to"],
                priority=raw["priority"],
                audit_question=raw["audit_question"],
                follow_up_probe=raw["follow_up_probe"],
                rationale_risk=raw["rationale_risk"],
                expected_evidence=raw["expected_evidence"],
                sampling_triangulation=raw["sampling_triangulation"],
                primary_roles=raw["primary_roles"],
                regulatory_alignment=raw["regulatory_alignment"],
                red_flags=raw["red_flags"],
                category=FindingCategory(raw["category"]),
                expected_document_types=tuple(raw["expected_document_types"]),
            )
        )
    return tuple(questions)
