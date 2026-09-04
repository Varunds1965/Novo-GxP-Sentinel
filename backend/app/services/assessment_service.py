"""Assessment service orchestrates the deterministic core.

Thin persistence layer over the real M0-M3 engine: it seeds the local
evidence store from the mentor corpus, evaluates all 350 checklist questions
with `ChecklistEngine` in `DETERMINISTIC_FALLBACK` mode, persists the findings
and readiness snapshot, and exposes them to the API. No model call and no
wall-clock read happens here (PRIN-R-013, ARCH-R-008).
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.database.seed_corpus import load_checklists, seed_corpus
from app.domain.clock import ClockPort, SystemClock
from app.domain.enums import (
    ApprovalStatus,
    AssessmentStatus,
    ConfidenceLevel,
    FindingStatus,
    RuntimeMode,
    Severity,
    TrustLevel,
)
from app.domain.errors import NotFoundError
from app.domain.hashing import sha256_text
from app.domain.models import Assessment, Finding, ReadinessScore
from app.rag.retrieval import Fts5Retrieval
from app.rules.applicability import derive_position
from app.rules.checklist_engine import ChecklistEngine, CorpusIndex
from app.rules.readiness import compute


class AssessmentService:
    """Manages assessment lifecycle and orchestrates the deterministic engine."""

    def __init__(
        self,
        db_connection,
        *,
        corpus_dir,
        checklists_path,
        clock: ClockPort | None = None,
    ):
        self.db = db_connection
        self._corpus_dir = Path(corpus_dir)
        self._checklists_path = Path(checklists_path)
        self._clock = clock or SystemClock()
        self._retrieval = Fts5Retrieval(db_connection)
        self._seeded = False

    def _ensure_store(self) -> None:
        """Seed the corpus into this database connection once (idempotent)."""
        if self._seeded:
            return
        if self._retrieval.count() == 0:
            seeded = seed_corpus(self._corpus_dir, self._retrieval, self._clock)
            self._persist_sources(seeded.sources)
        self._seeded = True

    def _persist_sources(self, sources) -> None:
        """Copy seeded SourceRecords into the `evidence` provenance tables."""
        now = self._clock.now().isoformat()
        for source in sources:
            self.db.execute(
                """
                INSERT OR IGNORE INTO evidence (
                    id, source_id, title, document_type, system_id, version,
                    approval_status, trust_level, content_hash, source_system,
                    ingested_at, effective_date, review_date, owner,
                    confidentiality, byte_size, page_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source.source_id, source.source_id, source.title,
                    source.document_type, source.system_id, source.version,
                    source.approval_status.value, source.trust_level.value,
                    source.content_hash, source.source_system,
                    source.ingested_at.isoformat(),
                    source.effective_date.isoformat() if source.effective_date else None,
                    source.review_date.isoformat() if source.review_date else None,
                    source.owner, source.confidentiality, source.byte_size,
                    source.page_count,
                ),
            )
            for finding in source.injection_findings:
                self.db.execute(
                    "INSERT OR IGNORE INTO evidence_injection_findings "
                    "(id, evidence_id, finding, severity, created_at)"
                    " VALUES (?, ?, ?, 'INFO', ?)",
                    (f"inj-{source.source_id}-{finding}", source.source_id,
                     finding, now),
                )
        rows = self.db.execute(
            "SELECT chunk_id, source_id, ordinal, location, body FROM chunk"
        ).fetchall()
        for row in rows:
            self.db.execute(
                "INSERT OR IGNORE INTO evidence_chunks "
                "(id, evidence_id, chunk_number, content, content_hash,"
                " location, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (row["chunk_id"], row["source_id"], row["ordinal"],
                 row["body"], sha256_text(row["body"]), row["location"], now),
            )
        self.db.commit()

    # -- section: engine helpers ----------------------------------------- #

    def _agent_findings(self, assessment_id: str, system_id: str) -> tuple:
        """Evaluate all 350 controls deterministically."""
        now = self._clock.now()
        questions = load_checklists(self._checklists_path)
        corpus = CorpusIndex.build(system_id, self._sources())
        position = derive_position(frozenset(corpus.sources_by_type))
        engine = ChecklistEngine(
            self._retrieval, corpus,
            mode=RuntimeMode.DETERMINISTIC_FALLBACK,
            position=position,
        )
        return tuple(engine.evaluate(q, now=now, task_id=assessment_id) for q in questions)

    def _sources(self) -> tuple:
        """Rebuild SourceRecord objects from the persisted evidence table."""
        from app.domain.models import SourceRecord

        rows = self.db.execute("SELECT * FROM evidence").fetchall()
        sources = []
        for row in rows:
            sources.append(
                SourceRecord(
                    source_id=row["source_id"],
                    title=row["title"],
                    document_type=row["document_type"],
                    system_id=row["system_id"],
                    version=row["version"],
                    approval_status=ApprovalStatus(row["approval_status"]),
                    trust_level=TrustLevel(row["trust_level"]),
                    content_hash=row["content_hash"],
                    source_system=row["source_system"],
                    ingested_at=datetime.fromisoformat(row["ingested_at"]),
                    effective_date=(
                        datetime.fromisoformat(row["effective_date"])
                        if row["effective_date"] else None
                    ),
                    review_date=(
                        datetime.fromisoformat(row["review_date"])
                        if row["review_date"] else None
                    ),
                    owner=row["owner"],
                    confidentiality=row["confidentiality"] or "Internal - Synthetic",
                    byte_size=row["byte_size"],
                    page_count=row["page_count"],
                )
            )
        return tuple(sources)

    # ------------------------------------------------------------------ #
    # Assessment lifecycle
    # ------------------------------------------------------------------ #

    def start_assessment(self, system_id: str, user_id: str) -> Assessment:
        """Create a new assessment."""
        self._ensure_store()
        assessment = Assessment(
            id=f"assess_{datetime.now().strftime('%Y%m%dT%H%M%S')}_{uuid.uuid4().hex[:6]}",
            system_id=system_id,
            user_id=user_id,
            status=AssessmentStatus.PENDING,
            created_at=self._clock.now(),
            mode=RuntimeMode.DETERMINISTIC_FALLBACK,
        )
        self.db.execute(
            """
            INSERT INTO assessments (id, system_id, user_id, status, created_at, mode)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                assessment.id, system_id, user_id, assessment.status.value,
                assessment.created_at.isoformat(), assessment.mode.value,
            ),
        )
        self.db.commit()
        return assessment

    def run_assessment(self, assessment_id: str) -> list[Finding]:
        """
        Execute the 350-control assessment with the deterministic engine.

        The engine owns every finding, severity and confidence level; the
        service only persists what the engine produced.
        """

        self._ensure_store()
        row = self.db.execute(
            "SELECT system_id FROM assessments WHERE id = ?", (assessment_id,)
        ).fetchone()
        if not row:
            raise NotFoundError(f"Assessment {assessment_id} not found")

        self.db.execute(
            "UPDATE assessments SET status = ? WHERE id = ?",
            (AssessmentStatus.RUNNING.value, assessment_id),
        )
        self.db.commit()

        now = self._clock.now()
        try:
            agent_findings = self._agent_findings(assessment_id, row["system_id"])
            findings = [
                Finding.from_agent_finding(f, assessment_id=assessment_id, created_at=now)
                for f in agent_findings
            ]
            for finding in findings:
                self._store_finding(finding)

            indicator = compute(row["system_id"], agent_findings, now=now)

            self._store_readiness(assessment_id, indicator)

            self.db.execute(
                "UPDATE assessments SET status = ?, completed_at = ? WHERE id = ?",
                (AssessmentStatus.COMPLETE.value, now.isoformat(), assessment_id),
            )
            self.db.commit()
            return findings
        except Exception:
            self.db.execute(
                "UPDATE assessments SET status = ? WHERE id = ?",
                (AssessmentStatus.FAILED.value, assessment_id),
            )
            self.db.commit()
            raise

    def get_assessment(self, assessment_id: str) -> Optional[Assessment]:
        """Fetch assessment metadata."""
        row = self.db.execute(
            "SELECT id, system_id, user_id, status, created_at, completed_at, mode"
            " FROM assessments WHERE id = ?",
            (assessment_id,),
        ).fetchone()
        if not row:
            return None
        return Assessment(
            id=row["id"],
            system_id=row["system_id"],
            user_id=row["user_id"],
            status=AssessmentStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            completed_at=(
                datetime.fromisoformat(row["completed_at"])
                if row["completed_at"] else None
            ),
            mode=RuntimeMode(row["mode"]),
        )

    def get_findings(self, assessment_id: str) -> list[Finding]:
        """Fetch all findings for an assessment."""
        rows = self.db.execute(
            "SELECT id, assessment_id, control_id, finding, severity, confidence,"
            " evidence_refs, status, created_at FROM findings WHERE assessment_id = ?"
            " ORDER BY severity DESC, control_id",
            (assessment_id,),
        ).fetchall()
        findings = []
        for row in rows:
            evidence_refs = json.loads(row["evidence_refs"]) if row["evidence_refs"] else []
            findings.append(
                Finding(
                    id=row["id"],
                    assessment_id=row["assessment_id"],
                    control_id=row["control_id"],
                    finding=row["finding"],
                    severity=Severity(int(row["severity"])),
                    confidence=ConfidenceLevel(row["confidence"]),
                    evidence_refs=tuple(evidence_refs),
                    status=FindingStatus(row["status"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
            )
        return findings

    def get_readiness_score(self, assessment_id: str) -> ReadinessScore:
        """Fetch the latest persisted readiness snapshot."""
        row = self.db.execute(
            "SELECT id, assessment_id, overall_score, status, dimensions, computed_at"
            " FROM readiness_scores WHERE assessment_id = ? ORDER BY computed_at DESC"
            " LIMIT 1",
            (assessment_id,),
        ).fetchone()
        if not row:
            raise NotFoundError(f"No readiness snapshot for {assessment_id}")
        return ReadinessScore(
            id=row["id"],
            assessment_id=row["assessment_id"],
            overall_score=row["overall_score"],
            status=row["status"],
            dimensions=tuple(json.loads(row["dimensions"])) if row["dimensions"] else (),
            computed_at=datetime.fromisoformat(row["computed_at"]),
        )

    def search_evidence(self, query: str, limit: int = 20) -> list[dict]:
        """Search evidence using FTS5 with provenance-aware re-ranking."""
        self._ensure_store()
        metadata = self._evidence_metadata()
        hits = self._retrieval.search(query, limit=limit, source_metadata=metadata)
        return [
            {
                "chunk_id": h.chunk_id,
                "source_id": h.source_id,
                "location": h.location,
                "body": h.body,
                "bm25": h.bm25,
                "rerank_score": h.rerank_score,
                "rerank_basis": h.rerank_basis,
            }
            for h in hits
        ]

    def _evidence_metadata(self) -> dict:
        """Map source_id -> (approval, trust, current) for retrieval re-rank."""
        now = self._clock.now()
        rows = self.db.execute(
            "SELECT source_id, approval_status, trust_level, review_date FROM evidence"
        ).fetchall()
        out: dict = {}
        for row in rows:
            current = row["review_date"] is None or datetime.fromisoformat(row["review_date"]) >= now
            out[row["source_id"]] = (
                ApprovalStatus(row["approval_status"]),
                TrustLevel(row["trust_level"]),
                current,
            )
        return out

    # -- persistence helpers ---------------------------------------------- #

    def _store_finding(self, finding: Finding) -> None:
        self.db.execute(
            """
            INSERT OR REPLACE INTO findings (
                id, assessment_id, control_id, finding, severity, confidence,
                evidence_refs, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                finding.id, finding.assessment_id, finding.control_id,
                finding.finding, finding.severity.value,
                finding.confidence.value,
                json.dumps(finding.evidence_refs),
                finding.status.value,
                finding.created_at.isoformat(),
            ),
        )
        self.db.commit()

    def _store_readiness(self, assessment_id: str, indicator) -> None:
        score = ReadinessScore.from_indicator(
            row_id=f"rs-{uuid.uuid4().hex[:12]}",
            assessment_id=assessment_id,
            indicator=indicator,
        )
        self.db.execute(
            """
            INSERT INTO readiness_scores (
                id, assessment_id, overall_score, status, dimensions, computed_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                score.id, score.assessment_id, score.overall_score, score.status,
                json.dumps(list(score.dimensions)),
                score.computed_at.isoformat(),
            ),
        )
        self.db.commit()