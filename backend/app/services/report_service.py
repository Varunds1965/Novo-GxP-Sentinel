"""Evidence-pack / report service (M9).

Builds an exportable evidence pack from persisted data only: assessment,
findings, readiness snapshot, evidence provenance, approvals and audit
events. A SHA-256 digest over the canonical JSON of the pack makes the
export tamper-evident. No field is invented: if data is missing it is
represented as missing.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime

from app.domain.errors import NotFoundError
from app.domain.hashing import canonical_json, sha256_text


class ReportService:
    """Assembles auditor-facing evidence packs from the live database."""

    def __init__(self, db_connection, *, clock=None):
        self.db = db_connection
        self._clock = clock

    def _now(self) -> str:
        if self._clock is not None:
            return self._clock.now().isoformat()
        return datetime.now().astimezone().isoformat()

    def build_evidence_pack(self, assessment_id: str, *, requested_by: str) -> dict:
        """Build the evidence pack for one assessment.

        Raises NotFoundError when the assessment does not exist.
        """
        assessment = self.db.execute(
            "SELECT * FROM assessments WHERE id = ?", (assessment_id,)
        ).fetchone()
        if assessment is None:
            raise NotFoundError(
                f"Assessment '{assessment_id}' does not exist; no evidence "
                "pack can be exported for it."
            )

        findings_rows = self.db.execute(
            "SELECT * FROM findings WHERE assessment_id = ? ORDER BY severity, id",
            (assessment_id,),
        ).fetchall()

        findings = []
        evidence_refs: dict[str, dict] = {}
        for row in findings_rows:
            refs = json.loads(row["evidence_refs"]) if row["evidence_refs"] else []
            findings.append(
                {
                    "id": row["id"],
                    "control_id": row["control_id"],
                    "finding": row["finding"],
                    "severity": row["severity"],
                    "confidence": row["confidence"],
                    "status": row["status"],
                    "created_at": row["created_at"],
                    "evidence_refs": refs,
                }
            )
            for ref in refs:
                source_id = ref.get("source_id")
                if source_id and source_id not in evidence_refs:
                    evidence_refs[source_id] = self._evidence_provenance(source_id)

        readiness = self.db.execute(
            "SELECT * FROM readiness_scores WHERE assessment_id = ?"
            " ORDER BY computed_at DESC LIMIT 1",
            (assessment_id,),
        ).fetchone()
        readiness_block = None
        if readiness is not None:
            readiness_block = {
                "id": readiness["id"],
                "overall_score": readiness["overall_score"],
                "status": readiness["status"],
                "dimensions": (
                    json.loads(readiness["dimensions"])
                    if readiness["dimensions"] else {}
                ),
                "computed_at": readiness["computed_at"],
            }

        approvals = [
            {
                "id": row["id"],
                "requested_by": row["requested_by"],
                "decided_by": row["decided_by"],
                "decision": row["decision"],
                "decision_note": row["decision_note"],
                "decided_at": row["decided_at"],
                "created_at": row["created_at"],
            }
            for row in self.db.execute(
                "SELECT * FROM approvals WHERE proposal_id = ? ORDER BY created_at",
                (assessment_id,),
            ).fetchall()
        ]

        audit_events = [
            {
                "id": row["id"],
                "user_id": row["user_id"],
                "action": row["action"],
                "resource_type": row["resource_type"],
                "resource_id": row["resource_id"],
                "details": row["details"],
                "result": row["result"],
                "timestamp": row["timestamp"],
            }
            for row in self.db.execute(
                "SELECT * FROM audit_log WHERE resource_id = ?"
                " OR resource_id IN (SELECT id FROM findings WHERE"
                " assessment_id = ?) ORDER BY timestamp",
                (assessment_id, assessment_id),
            ).fetchall()
        ]

        pack = {
            "pack_id": f"pack-{uuid.uuid4().hex[:12]}",
            "generated_at": self._now(),
            "requested_by": requested_by,
            "assessment": {
                "id": assessment["id"],
                "system_id": assessment["system_id"],
                "status": assessment["status"],
                "created_at": assessment["created_at"],
                "completed_at": assessment["completed_at"],
                "mode": assessment["mode"],
            },
            "findings": findings,
            "findings_total": len(findings),
            "readiness": readiness_block,
            "evidence_provenance": evidence_refs,
            "approvals": approvals,
            "audit_events": audit_events,
            "disclaimer": (
                "Deterministic export assembled from persisted records. "
                "Contains no model-generated assertions."
            ),
        }
        pack["sha256"] = sha256_text(canonical_json(pack))
        return pack

    def _evidence_provenance(self, source_id: str) -> dict:
        row = self.db.execute(
            "SELECT source_id, title, document_type, system_id, version,"
            " approval_status, trust_level, content_hash, ingested_at,"
            " confidentiality FROM evidence WHERE source_id = ?",
            (source_id,),
        ).fetchone()
        if row is None:
            return {
                "source_id": source_id,
                "present": False,
                "note": "referenced by a finding but not present in the"
                        " evidence store",
            }
        chunk_count = self.db.execute(
            "SELECT COUNT(*) FROM evidence_chunks WHERE evidence_id = ?",
            (source_id,),
        ).fetchone()[0]
        return {
            "source_id": source_id,
            "present": True,
            "title": row["title"],
            "document_type": row["document_type"],
            "system_id": row["system_id"],
            "version": row["version"],
            "approval_status": row["approval_status"],
            "trust_level": row["trust_level"],
            "content_hash": row["content_hash"],
            "ingested_at": row["ingested_at"],
            "confidentiality": row["confidentiality"],
            "chunk_count": int(chunk_count),
        }

