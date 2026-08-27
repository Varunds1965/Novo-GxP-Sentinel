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
