"""Immutable domain models.

All models are frozen dataclasses with zero I/O and zero framework imports
(ARCH-R-002). They can be imported by a bare interpreter, which is the
mechanical test that the layering has not been broken.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Mapping

from app.domain.enums import (
    ActionType,
    AgentId,
    Applicability,
    ApprovalStatus,
    AssessmentStatus,
    AuditConclusion,
    ConfidenceLevel,
    Currency,
    EdgeType,
    EvidenceState,
    FindingCategory,
    FindingStatus,
    MaturityScore,
    NodeType,
    PolicyReason,
    ProposalStatus,
    Role,
    RuntimeMode,
    Severity,
    TrustLevel,
)

SCHEMA_VERSION = "1.0"


@dataclass(frozen=True, slots=True)
class User:
    """Authenticated user with role."""
    id: str
    username: str
    role_id: str  # Foreign key to Role
    created_at: datetime | None = None
    
    @property
    def role(self) -> Role | None:
        """Role property for auth_service compatibility."""
        try:
            return Role(self.role_id)
        except (ValueError, KeyError):
            return None


@dataclass(frozen=True, slots=True)
class SourceRecord:
    """A single ingested evidence source with full provenance (PRIN-R-012)."""

    source_id: str
    title: str
    document_type: str
    system_id: str
    version: str
    approval_status: ApprovalStatus
    trust_level: TrustLevel
    content_hash: str
    source_system: str
    ingested_at: datetime
    effective_date: datetime | None = None
    review_date: datetime | None = None
    owner: str | None = None
    confidentiality: str = "Internal - Synthetic"
    byte_size: int = 0
    page_count: int = 0
    injection_findings: tuple[str, ...] = ()

    def currency(self, now: datetime) -> Currency:
        if self.review_date is None:
            return Currency.NO_REVIEW_DATE
        if self.review_date < now:
            return Currency.EXPIRED
        return Currency.CURRENT

    @property
    def is_quarantined(self) -> bool:
        return self.trust_level is TrustLevel.QUARANTINED_UNTRUSTED


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    """Typed, hashed pointer into one location of one source version.

    `relevant_excerpt` is always verbatim source text. Model-generated summary
    text in this field is a data-integrity violation (AGENT-R-005).
    """

    source_id: str
    title: str
    location: str
    content_hash: str
    version: str
    approval_status: ApprovalStatus
    trust_level: TrustLevel
    relevant_excerpt: str
    retrieved_at: datetime
    effective_date: datetime | None = None
    review_date: datetime | None = None
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if len(self.relevant_excerpt) > 600:
            raise ValueError(
                f"EvidenceRef excerpt for {self.source_id} exceeds 600 chars; "
                "excerpts must be citable, not whole documents"
            )


@dataclass(frozen=True, slots=True)
class ChecklistQuestion:
    """One of the 350 auditor questions (DA-<phase>-<seq>)."""

    q_id: str
    phase_no: int
    lifecycle_phase: str
    sequence: int
    audit_domain: str
    control_topic: str
    applies_to: str
    priority: str
    audit_question: str
    follow_up_probe: str
    rationale_risk: str
    expected_evidence: str
    sampling_triangulation: str
    primary_roles: str
    regulatory_alignment: str
    red_flags: str
    category: FindingCategory
    expected_document_types: tuple[str, ...] = ()

    @property
    def is_critical(self) -> bool:
        return self.priority.upper() == "CRITICAL"


@dataclass(frozen=True, slots=True)
class ConfidenceAssessment:
    """Deterministic confidence, never model self-report (GXP-R-013)."""

    level: ConfidenceLevel
    coverage: float
    basis: str
    factors: Mapping[str, float] = field(default_factory=dict)
    uncertainty: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.coverage <= 1.0:
            raise ValueError(f"coverage must be within 0..1, got {self.coverage}")


@dataclass(frozen=True, slots=True)
class AgentFinding:
    """A deterministic control outcome, presented to users as a gap."""

    finding_id: str
    task_id: str
    agent_id: AgentId
    system_id: str
    category: FindingCategory
    severity: Severity
    claim: str
    evidence: tuple[EvidenceRef, ...]
    evidence_state: EvidenceState
    confidence: ConfidenceAssessment
    conclusion: AuditConclusion
    maturity_score: MaturityScore
    recommended_action: str
    requires_human_approval: bool
    status: FindingStatus
    generation_mode: RuntimeMode
    rule_id: str
    applicability: Applicability = Applicability.APPLICABLE
    applicability_basis: str = ""
    checklist_q_ids: tuple[str, ...] = ()
    regulatory_refs: tuple[str, ...] = ()
    narrative: str = ""
    narrative_source: str = "deterministic-template"
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        # PRIN-R-010: a material claim carries evidence or an explicit
        # insufficient-evidence marker. There is no third option.
        if not self.evidence and self.confidence.level is not ConfidenceLevel.INSUFFICIENT_EVIDENCE:
            raise ValueError(
                f"{self.finding_id}: finding without evidence must be marked "
                "INSUFFICIENT_EVIDENCE (PRIN-R-010)"
            )

    def with_confidence(self, assessment: ConfidenceAssessment) -> "AgentFinding":
        return replace(self, confidence=assessment)


@dataclass(frozen=True, slots=True)
class DryRunResult:
    would_succeed: bool
    description: str
    preconditions_met: tuple[str, ...] = ()
    preconditions_failed: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ActionProposal:
    """A proposed write. Constructing one is not executing it (ARCH-R-025)."""

    proposal_id: str
    requested_by_agent: AgentId
    user_id: str
    user_role: Role
    action_type: ActionType
    target_system: str
    target_record: str
    operation: str
    parameters: Mapping[str, str | int | bool]
    gxp_relevant: bool
    risk_level: Severity
    impact: str
    preconditions: tuple[str, ...]
    dry_run_result: DryRunResult
    approval_required: bool
    rollback_or_compensation: str
    status: ProposalStatus
    created_at: datetime
    trace_id: str
    evidence: tuple[EvidenceRef, ...] = ()
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for key, value in self.parameters.items():
            if not isinstance(value, (str, int, bool)):
                raise TypeError(
                    f"proposal parameter {key!r} must be a scalar so it renders "
                    "as one row of the approval dialog (AGENT-R-004)"
                )


@dataclass(frozen=True, slots=True)
class ApprovalDecision:
    approval_id: str
    proposal_id: str
    proposal_hash: str
    decided_by: str
    decided_by_role: Role
    decision: ProposalStatus
    decision_note: str
    decided_at: datetime
    trace_id: str

    def __post_init__(self) -> None:
        # UI-R-021 is enforced server-side as well as in the browser.
        if len(self.decision_note.strip()) < 10:
            raise ValueError("a decision note of at least 10 characters is required")


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    allowed: bool
    reason_code: PolicyReason
    human_message: str
    obligations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class GraphNode:
    node_id: str
    node_type: NodeType
    label: str
    attributes: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class GraphEdge:
    source: str
    target: str
    edge_type: EdgeType
    attributes: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ReadinessDimension:
    key: str
    label: str
    percentage: int
    caption: str
    weight: float


@dataclass(frozen=True, slots=True)
class ReadinessIndicator:
    """Explainable composite indicator. Never a compliance certification."""

    system_id: str
    score: int
    verdict: str
    open_findings: int
    critical_findings: int
    dimensions: tuple[ReadinessDimension, ...]
    calculation: Mapping[str, float]
    computed_at: datetime
    disclaimer: str = "Not a compliance certification."


def evidence_ref_to_dict(ref: EvidenceRef) -> dict[str, object]:
    """One row of the findings table's `evidence_refs` JSON column.

    Dates are serialised to ISO-8601 strings so the value is directly
    JSON-serialisable and remains provenance-complete (PRIN-R-012).
    """
    return {
        "source_id": ref.source_id,
        "title": ref.title,
        "location": ref.location,
        "content_hash": ref.content_hash,
        "version": ref.version,
        "approval_status": ref.approval_status.value,
        "trust_level": ref.trust_level.value,
        "relevant_excerpt": ref.relevant_excerpt,
        "retrieved_at": ref.retrieved_at.astimezone().isoformat(),
    }


@dataclass(frozen=True, slots=True)
class Assessment:
    """A persisted assessment run over one system's checklist (M3 row model)."""

    id: str
    system_id: str
    user_id: str
    status: AssessmentStatus
    created_at: datetime
    completed_at: datetime | None = None
    mode: RuntimeMode = RuntimeMode.DETERMINISTIC_FALLBACK


@dataclass(frozen=True, slots=True)
class Finding:
    """A persisted finding row, mirroring the `findings` table.

    `severity` and `confidence` are the closed enums defined in this domain;
    `evidence_refs` is a tuple of the JSON-compatible dicts produced by
    `evidence_ref_to_dict` so the row round-trips without a framework.
    """

    id: str
    assessment_id: str
    control_id: str
    finding: str
    severity: Severity
    confidence: ConfidenceLevel
    evidence_refs: tuple[dict[str, object], ...] = ()
    status: FindingStatus = FindingStatus.OPEN
    created_at: datetime | None = None

    @classmethod
    def from_agent_finding(
        cls,
        finding: AgentFinding,
        *,
        assessment_id: str,
        created_at: datetime,
    ) -> "Finding":
        # The engine's finding_id is deterministic per control (FND-<q_id>);
        # the persisted primary key is scoped to the assessment so that two
        # assessments of the same system never collide, while a re-run of the
        # same assessment stays idempotent (same id, replaced row).
        return cls(
            id=f"{assessment_id}:{finding.finding_id}",
            assessment_id=assessment_id,
            control_id=finding.checklist_q_ids[0] if finding.checklist_q_ids else "",
            finding=finding.claim,
            severity=finding.severity,
            confidence=finding.confidence.level,
            evidence_refs=tuple(evidence_ref_to_dict(ref) for ref in finding.evidence),
            status=finding.status,
            created_at=created_at,
        )


@dataclass(frozen=True, slots=True)
class ReadinessScore:
    """A persisted readiness snapshot (`readiness_scores` row model)."""

    id: str
    assessment_id: str
    overall_score: int
    status: str
    dimensions: tuple[dict[str, object], ...] = ()
    computed_at: datetime | None = None

    @classmethod
    def from_indicator(
        cls,
        *,
        row_id: str,
        assessment_id: str,
        indicator: "ReadinessIndicator",
    ) -> "ReadinessScore":
        return cls(
            id=row_id,
            assessment_id=assessment_id,
            overall_score=indicator.score,
            status=indicator.verdict,
            dimensions=tuple(
                {
                    "key": d.key,
                    "label": d.label,
                    "percentage": d.percentage,
                    "caption": d.caption,
                    "weight": d.weight,
                }
                for d in indicator.dimensions
            ),
            computed_at=indicator.computed_at,
        )
