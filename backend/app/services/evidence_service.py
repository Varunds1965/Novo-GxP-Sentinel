"""Evidence ingestion service (M5 upload boundary over the 12-step pipeline).

Uploaded content follows the same ingestion pipeline the corpus seeder uses:
name hygiene, extension allowlist, size ceiling, magic-byte sniff, raw-bytes
hash, duplicate detection, bounded extraction, prompt-injection scan, trust
assignment, provenance capture. Quarantined content is never indexed and never
retrievable (SEC-R-015/016).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from app.domain.clock import ClockPort, SystemClock
from app.domain.enums import TrustLevel
from app.domain.hashing import sha256_text
from app.rag.extractors.office import default_extractors
from app.rag.ingestion import IngestionPipeline
from app.rag.retrieval import Fts5Retrieval


class EvidenceService:
    """Persists uploaded evidence and indexes it for retrieval."""

    def __init__(self, db_connection, *, clock: ClockPort | None = None):
        self.db = db_connection
        self._clock = clock or SystemClock()
        self._pipeline = IngestionPipeline(self._clock, default_extractors())
        self._retrieval = Fts5Retrieval(db_connection)
        self._known_hashes = self._load_known_hashes()

    def _load_known_hashes(self) -> dict:
        rows = self.db.execute("SELECT source_id, content_hash FROM evidence").fetchall()
        return {row["content_hash"]: row["source_id"] for row in rows}

    def ingest(
        self,
        *,
        filename: str,
        payload: bytes,
        uploaded_by: str,
        system_id: str,
        document_type: str = "UPLOADED_EVIDENCE",
    ) -> dict:
        """Run the full pipeline and persist the outcome."""
        outcome = self._pipeline.ingest(
            filename=filename,
            payload=payload,
            system_id=system_id,
            uploaded_by=uploaded_by,
            document_type=document_type,
        )
        record = outcome.record
        now = self._clock.now()
        if outcome.duplicate_of is not None:
            return {
                "source_id": outcome.duplicate_of,
                "title": record.title,
                "trust_level": record.trust_level.value,
                "quarantined": record.is_quarantined,
                "indexed": False,
                "chunks_indexed": 0,
                "duplicate_of": outcome.duplicate_of,
                "injection_findings": list(record.injection_findings),
            }

        self.db.execute(
            """
            INSERT INTO evidence (
                id, source_id, title, document_type, system_id, version,
                approval_status, trust_level, content_hash, source_system,
                ingested_at, effective_date, review_date, owner,
                confidentiality, byte_size, page_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.source_id, record.source_id, record.title,
                record.document_type, record.system_id, record.version,
                record.approval_status.value, record.trust_level.value,
                record.content_hash, record.source_system,
                record.ingested_at.isoformat(), None, None,
                record.owner, record.confidentiality, record.byte_size,
                record.page_count,
            ),
        )
        for finding in record.injection_findings:
            self.db.execute(
                "INSERT OR IGNORE INTO evidence_injection_findings "
                "(id, evidence_id, finding, severity, created_at)"
                " VALUES (?, ?, ?, 'INFO', ?)",
                (f"inj-{record.source_id}-{finding}", record.source_id,
                 finding, now.isoformat()),
            )

        indexed = 0
        if record.is_quarantined:
            chunks = ()
        else:
            chunks = outcome.chunks
            indexed = self._retrieval.index_chunks(chunks)
            for chunk in chunks:
                self.db.execute(
                    "INSERT OR IGNORE INTO evidence_chunks "
                    "(id, evidence_id, chunk_number, content, content_hash,"
                    " location, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (chunk.chunk_id, record.source_id, chunk.ordinal,
                     chunk.text, sha256_text(chunk.text), chunk.location,
                     now.isoformat()),
                )
            self._known_hashes[record.content_hash] = record.source_id
        self.db.commit()

        return {
            "source_id": record.source_id,
            "title": record.title,
            "document_type": record.document_type,
            "version": record.version,
            "system_id": record.system_id,
            "trust_level": record.trust_level.value,
            "quarantined": record.is_quarantined,
            "indexed": indexed > 0,
            "chunks_indexed": indexed,
            "duplicate_of": None,
            "injection_findings": list(record.injection_findings),
            "ingested_at": record.ingested_at.isoformat(),
            "content_hash": record.content_hash,
        }