"""Deterministic evaluation of audit-checklist questions against the corpus.

This module is the compliance engine. It contains no model call, no randomness
and no wall-clock read (PRIN-R-013, ARCH-R-008). Given the same corpus and the
same frozen clock it produces byte-identical findings, which is what makes
`DETERMINISTIC_FALLBACK` indistinguishable from `LOCAL_AI` in every respect
that matters (AGENT-R-036).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from app.domain.enums import (
    AgentId,
    Applicability,
    ApprovalStatus,
    AuditConclusion,
    ConfidenceLevel,
    Currency,
    EvidenceState,
    FindingCategory,
    FindingStatus,
    MaturityScore,
    RuntimeMode,
    Severity,
    TrustLevel,
)
from app.domain.models import (
    AgentFinding,
    ChecklistQuestion,
    EvidenceRef,
    SourceRecord,
)
from app.rules.applicability import SystemLifecyclePosition, derive_position
from app.rules.confidence import ClaimPolarity, assess
from app.rules.readiness import maturity_from_state

# Documents whose presence constitutes EXECUTED evidence rather than intent.
# An approved plan says what will happen; these say what did happen.
EXECUTION_DOC_TYPES = frozenset(
    {"IQR", "IQTC", "IRTR", "BRVR", "AMRR", "ATR", "INC", "DEVL", "DEFL", "CHG",
     "ITPSE", "URR", "DRR", "IREP", "VSR", "TRN"}
)

# Which agent owns which finding category (ARCH-R-024).
CATEGORY_OWNER: dict[FindingCategory, AgentId] = {
    FindingCategory.DOCUMENTATION: AgentId.A2_AUDIT,
    FindingCategory.VALIDATION: AgentId.A2_AUDIT,
    FindingCategory.TRACEABILITY: AgentId.A2_AUDIT,
    FindingCategory.PERIODIC_REVIEW: AgentId.A2_AUDIT,
    FindingCategory.RISK: AgentId.A3_RISK,
    FindingCategory.SUPPLIER: AgentId.A3_RISK,
    FindingCategory.CHANGE: AgentId.A4_CHANGE,
    FindingCategory.BACKUP: AgentId.A4_CHANGE,
    FindingCategory.INCIDENT: AgentId.A5_INCIDENT,
    FindingCategory.ACCESS: AgentId.A6_ACCESS,
    FindingCategory.DATA_INTEGRITY: AgentId.A1_KNOWLEDGE,
    FindingCategory.TRAINING: AgentId.A1_KNOWLEDGE,
}

_STOP = frozenset(
    """a an the and or of to in for on with is are was were be been by as at from that this it
    its any all show me give please tell what which who whom how why when do does did our we
    you your walk through demonstrate explain describe present identify confirm select trace""".split()
)
_TOKEN = re.compile(r"[a-z][a-z0-9\-]{3,}")

# Red-flag phrases that indicate a control is asserted but not evidenced.
_CLAIM_ONLY_MARKERS = (
    "planned", "proposed", "not activated", "to be confirmed", "verify item",
    "would be", "intended to", "future state", "not yet", "placeholder", "tbd",
)
_OPEN_MARKERS = ("open", "not in control", "overdue", "unresolved", "pending", "rejected")

# BM25-derived relevance floors. Below these a chunk is a coincidental token
# match rather than evidence about the control question.
#
# Tier 1 searches only the artefact types the question expects, so a moderate
# floor is safe. Tier 2 searches the whole corpus and therefore uses a much
# higher floor: it exists to answer "does relevant content exist anywhere, even
# though the expected artefact is absent?", which is a materially different and
# weaker finding than "the expected artefact is present and current". Recording
# which tier produced the evidence keeps that distinction visible to a reviewer
# instead of hiding it inside a single grounding percentage.
MIN_RELEVANCE_SCORE = 4.0
MIN_RELEVANCE_SCORE_TIER2 = 9.0


@dataclass(frozen=True, slots=True)
class CorpusIndex:
    """Read-only projection of the evidence store used by the engine."""

    system_id: str
    sources_by_type: dict[str, tuple[SourceRecord, ...]]
    all_sources: tuple[SourceRecord, ...]

    @classmethod
    def build(cls, system_id: str, sources: tuple[SourceRecord, ...]) -> "CorpusIndex":
        by_type: dict[str, list[SourceRecord]] = {}
        for source in sources:
            by_type.setdefault(source.document_type, []).append(source)
        return cls(
            system_id=system_id,
            sources_by_type={k: tuple(v) for k, v in by_type.items()},
            all_sources=sources,
        )

    def of_types(self, doc_types: tuple[str, ...]) -> tuple[SourceRecord, ...]:
        found: list[SourceRecord] = []
        for doc_type in doc_types:
            found.extend(self.sources_by_type.get(doc_type, ()))
        return tuple(found)


def keywords(text: str, limit: int = 12) -> tuple[str, ...]:
    seen: list[str] = []
    for token in _TOKEN.findall(text.lower()):
        if token not in _STOP and token not in seen:
            seen.append(token)
    return tuple(seen[:limit])


def _excerpt(body: str, terms: tuple[str, ...], width: int = 320) -> str:
    lowered = body.lower()
    best = -1
    for term in terms:
        position = lowered.find(term)
        if position != -1 and (best == -1 or position < best):
            best = position
    start = max(0, (best if best != -1 else 0) - 40)
    return re.sub(r"\s+", " ", body[start : start + width]).strip()


class ChecklistEngine:
    """Evaluates one checklist question at a time. Pure apart from retrieval."""

    def __init__(
        self,
        retrieval,
        corpus: CorpusIndex,
        *,
        mode: RuntimeMode,
        position: SystemLifecyclePosition | None = None,
    ) -> None:
        self._retrieval = retrieval
        self._corpus = corpus
        self._mode = mode
        self._position = position or derive_position(frozenset(corpus.sources_by_type))
        self._metadata = {
            s.source_id: (s.approval_status, s.trust_level, False) for s in corpus.all_sources
        }
        self._by_id = {s.source_id: s for s in corpus.all_sources}

    def evaluate(
        self,
        question: ChecklistQuestion,
        *,
        now: datetime,
        task_id: str,
        max_evidence: int = 4,
    ) -> AgentFinding:
        applicability, applicability_basis = self._position.assess(question.phase_no)
        if applicability is not Applicability.APPLICABLE:
            return self._not_applicable(question, applicability, applicability_basis, now, task_id)

        expected = tuple(question.expected_document_types)
        candidates = self._corpus.of_types(expected)
        terms = keywords(f"{question.control_topic} {question.audit_question}")

        hits = self._retrieval.search(
            f"{question.control_topic} {question.audit_question}",
            limit=max_evidence * 3,
            source_metadata=self._metadata,
        )
        candidate_ids = {s.source_id for s in candidates}
        # Evidence must be of an expected document type AND clear a relevance
        # floor. Backfilling with any topically-adjacent chunk would manufacture
        # grounding and let a question appear answered when the expected artefact
        # does not exist, which is precisely the coverage illusion the master SOP
        # requires us to defeat. When nothing qualifies, the finding is MISSING.
        ranked = [
            h for h in hits
            if h.source_id in candidate_ids and h.rerank_score >= MIN_RELEVANCE_SCORE
        ]
        evidence_tier = 1
        if not ranked:
            ranked = [h for h in hits if h.rerank_score >= MIN_RELEVANCE_SCORE_TIER2]
            evidence_tier = 2 if ranked else 0

        evidence: list[EvidenceRef] = []
        seen_sources: set[str] = set()
        for hit in ranked:
            source = self._by_id.get(hit.source_id)
            if source is None or source.is_quarantined:
                continue
            if hit.source_id in seen_sources:
                continue
            seen_sources.add(hit.source_id)
            evidence.append(
                EvidenceRef(
                    source_id=source.source_id,
                    title=source.title,
                    location=hit.location,
                    content_hash=source.content_hash,
                    version=source.version,
                    approval_status=source.approval_status,
                    trust_level=source.trust_level,
                    relevant_excerpt=_excerpt(hit.body, terms),
                    retrieved_at=now,
                    effective_date=source.effective_date,
                    review_date=source.review_date,
                )
            )
            if len(evidence) >= max_evidence:
                break

        evidence_tuple = tuple(evidence)
        missing_types = tuple(t for t in expected if not self._corpus.sources_by_type.get(t))
        off_type_evidence = evidence_tier == 2

        # --- deterministic evidence-state determination ------------------
        evidence_found = bool(evidence_tuple)
        approved = any(r.approval_status is ApprovalStatus.APPROVED for r in evidence_tuple)
        expired = any(
            r.review_date is not None and r.review_date < now for r in evidence_tuple
        )
        current = evidence_found and not expired
        execution_evidence = (not off_type_evidence) and any(
            self._by_id[r.source_id].document_type in EXECUTION_DOC_TYPES
            for r in evidence_tuple
        )
        corroborated = len({r.source_id for r in evidence_tuple}) >= 3

        joined = " ".join(r.relevant_excerpt.lower() for r in evidence_tuple)
        claim_only = any(marker in joined for marker in _CLAIM_ONLY_MARKERS)
        open_items = [marker for marker in _OPEN_MARKERS if marker in joined]
        contradicted = False

        maturity = maturity_from_state(
            evidence_found=evidence_found,
            approved=approved,
            current=current,
            execution_evidence=execution_evidence and not claim_only,
            corroborated=corroborated and not off_type_evidence,
            contradicted=contradicted,
        )
        if off_type_evidence:
            # Relevant content exists, but not in the artefact the control
            # expects. That is a located document at best, never demonstrated.
            maturity = min(maturity, MaturityScore.CLAIM_ONLY)

        if not evidence_found:
            state = EvidenceState.MISSING
        elif expired:
            state = EvidenceState.EXPIRED
        elif not approved:
            state = EvidenceState.UNAPPROVED
        elif claim_only or not execution_evidence:
            state = EvidenceState.NEEDS_REVIEW
        else:
            state = EvidenceState.PRESENT

        conclusion = {
            MaturityScore.ABSENT_OR_CONTRADICTED: AuditConclusion.NOT_DEMONSTRATED,
            MaturityScore.CLAIM_ONLY: AuditConclusion.NOT_DEMONSTRATED,
            MaturityScore.DOCUMENT_LOCATED: AuditConclusion.PARTIALLY_DEMONSTRATED,
            MaturityScore.DEMONSTRATED: AuditConclusion.DEMONSTRATED,
            MaturityScore.CORROBORATED_RESILIENT: AuditConclusion.DEMONSTRATED,
        }[maturity]
        if not evidence_found:
            conclusion = AuditConclusion.UNABLE_TO_DETERMINE

        polarity = (
            ClaimPolarity.GAP
            if maturity <= MaturityScore.DOCUMENT_LOCATED
            else ClaimPolarity.CONFORMANCE
        )
        missing_required = missing_types or (
            ("executed verification evidence",) if not execution_evidence else ()
        )
        confidence = assess(
            evidence_tuple,
            now=now,
            polarity=polarity,
            required_evidence_count=max(1, len(expected)),
            missing_required=missing_required,
            execution_evidence=execution_evidence and not claim_only,
        )

        severity = self._severity(question, maturity)
        claim = self._claim(question, maturity, state, missing_types, open_items)
        if off_type_evidence:
            claim = (
                f"{question.control_topic}: no artefact of the expected type "
                f"({', '.join(expected) or 'unmapped'}) was located. Relevant content "
                f"was found in {', '.join(sorted({e.source_id for e in evidence_tuple}))}, "
                "which evidences intent but is not the controlled artefact this "
                "question requires."
            )
        action = self._action(question, maturity, missing_types)

        return AgentFinding(
            finding_id=f"FND-{question.q_id}",
            task_id=task_id,
            agent_id=CATEGORY_OWNER[question.category],
            system_id=self._corpus.system_id,
            category=question.category,
            severity=severity,
            claim=claim,
            evidence=evidence_tuple,
            evidence_state=state,
            confidence=confidence,
            conclusion=conclusion,
            maturity_score=maturity,
            recommended_action=action,
            requires_human_approval=severity >= Severity.MEDIUM,
            status=(
                FindingStatus.INSUFFICIENT_EVIDENCE
                if confidence.level is ConfidenceLevel.INSUFFICIENT_EVIDENCE
                else FindingStatus.OPEN
                if severity >= Severity.MEDIUM
                else FindingStatus.CLOSED
            ),
            generation_mode=self._mode,
            rule_id=f"CHECKLIST::{question.q_id}::tier{evidence_tier}",
            checklist_q_ids=(question.q_id,),
            regulatory_refs=tuple(
                part.strip()
                for part in question.regulatory_alignment.split(";")
                if part.strip()
            )[:4],
            narrative="",
            narrative_source="deterministic-template",
            applicability=Applicability.APPLICABLE,
        )

    def _not_applicable(
        self,
        question: ChecklistQuestion,
        applicability: Applicability,
        basis: str,
        now: datetime,
        task_id: str,
    ) -> AgentFinding:
        """Report a not-yet-reached control honestly instead of as a gap."""
        return AgentFinding(
            finding_id=f"FND-{question.q_id}",
            task_id=task_id,
            agent_id=CATEGORY_OWNER[question.category],
            system_id=self._corpus.system_id,
            category=question.category,
            severity=Severity.INFO,
            claim=f"{question.control_topic}: not applicable at the current lifecycle phase.",
            evidence=(),
            evidence_state=EvidenceState.NEEDS_REVIEW,
            confidence=assess(
                (),
                now=now,
                polarity=ClaimPolarity.GAP,
                missing_required=(f"phase-{question.phase_no} artefacts",),
            ),
            conclusion=AuditConclusion.NOT_APPLICABLE_WITH_EVIDENCE,
            maturity_score=MaturityScore.DOCUMENT_LOCATED,
            recommended_action=(
                "No action now. Re-assess this control when the system reaches "
                f"{question.lifecycle_phase}."
            ),
            requires_human_approval=False,
            status=FindingStatus.CLOSED,
            generation_mode=self._mode,
            rule_id=f"APPLICABILITY::{question.q_id}",
            checklist_q_ids=(question.q_id,),
            applicability=applicability,
            applicability_basis=basis,
        )

    @staticmethod
    def _severity(question: ChecklistQuestion, maturity: MaturityScore) -> Severity:
        critical_question = question.is_critical
        if maturity is MaturityScore.ABSENT_OR_CONTRADICTED:
            return Severity.CRITICAL if critical_question else Severity.HIGH
        if maturity is MaturityScore.CLAIM_ONLY:
            return Severity.HIGH if critical_question else Severity.MEDIUM
        if maturity is MaturityScore.DOCUMENT_LOCATED:
            return Severity.MEDIUM if critical_question else Severity.LOW
        return Severity.INFO

    @staticmethod
    def _claim(
        question: ChecklistQuestion,
        maturity: MaturityScore,
        state: EvidenceState,
        missing_types: tuple[str, ...],
        open_items: list[str],
    ) -> str:
        topic = question.control_topic
        if maturity is MaturityScore.ABSENT_OR_CONTRADICTED:
            if missing_types:
                return (
                    f"{topic}: no indexed evidence of the expected type "
                    f"({', '.join(missing_types)}) exists for this system."
                )
            return f"{topic}: no indexed evidence addresses this control question."
        if maturity is MaturityScore.CLAIM_ONLY:
            return (
                f"{topic}: the corpus asserts the control but the located text is "
                "planned or proposed rather than executed, so it is a claim without "
                "objective evidence."
            )
        if maturity is MaturityScore.DOCUMENT_LOCATED:
            reason = {
                EvidenceState.EXPIRED: "the located evidence passed its review date",
                EvidenceState.UNAPPROVED: "the located evidence is draft or unapproved",
                EvidenceState.NEEDS_REVIEW: "no executed record corroborates the narrative",
            }.get(state, "the located evidence is incomplete")
            suffix = f" Open markers present: {', '.join(sorted(set(open_items)))}." if open_items else ""
            return f"{topic}: relevant evidence exists but {reason}.{suffix}"
        return f"{topic}: current approved evidence and executed records were located and reconciled."

    @staticmethod
    def _action(
        question: ChecklistQuestion, maturity: MaturityScore, missing_types: tuple[str, ...]
    ) -> str:
        if maturity is MaturityScore.ABSENT_OR_CONTRADICTED:
            base = "Produce and approve the missing evidence"
            if missing_types:
                base += f" of type {', '.join(missing_types)}"
            return f"{base}, then re-run this control check. Probe: {question.follow_up_probe[:180]}"
        if maturity <= MaturityScore.DOCUMENT_LOCATED:
            return (
                "Obtain approval and executed verification evidence, then reconcile "
                f"against the independent records named in the sampling guidance. "
                f"Probe: {question.follow_up_probe[:180]}"
            )
        return "No action required beyond retaining the evidence index for inspection."
