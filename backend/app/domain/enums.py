"""Closed enumerations for the GxP Sentinel domain.

Every closed set in the system is defined here exactly once. A stringly-typed
status anywhere else in the codebase is a defect (CODE-R-018).
"""

from __future__ import annotations

from enum import Enum, IntEnum


class StrEnum(str, Enum):
    """Serialises as its value; comparable to plain strings at boundaries."""

    def __str__(self) -> str:  # pragma: no cover - trivial
        return str(self.value)


class RuntimeMode(StrEnum):
    """The only two runtime modes permitted by the zero-key override."""

    LOCAL_AI = "LOCAL_AI"
    DETERMINISTIC_FALLBACK = "DETERMINISTIC_FALLBACK"


class AgentId(StrEnum):
    A0_SUPERVISOR = "A0"
    A1_KNOWLEDGE = "A1"
    A2_AUDIT = "A2"
    A3_RISK = "A3"
    A4_CHANGE = "A4"
    A5_INCIDENT = "A5"
    A6_ACCESS = "A6"
    A7_REMEDIATION = "A7"
    C1_VERIFIER = "C1"


class LifecycleState(StrEnum):
    """Macro lifecycle phases from the master SOP's evidence-gate model."""

    ANALYSE = "ANALYSE"
    IMPLEMENT = "IMPLEMENT"
    OPERATE = "OPERATE"
    RETIRE = "RETIRE"


class Applicability(StrEnum):
    """Why a control question is or is not in scope for this assessment."""

    APPLICABLE = "APPLICABLE"
    NOT_YET_REACHED = "NOT_YET_REACHED"
    CONDITION_NOT_PRESENT = "CONDITION_NOT_PRESENT"


class Role(StrEnum):
    """The five demonstration roles from the Visual User Manual."""

    SYSTEM_OWNER = "SYSTEM_OWNER"
    QA_REVIEWER = "QA_REVIEWER"
    AUDITOR = "AUDITOR"
    LEADERSHIP_VIEWER = "LEADERSHIP_VIEWER"
    SECURITY_TESTER = "SECURITY_TESTER"


class Permission(StrEnum):
    READ = "READ"
    EXPORT = "EXPORT"
    INGEST = "INGEST"
    PROPOSE = "PROPOSE"
    APPROVE = "APPROVE"
    RUN_ASSURANCE_LAB = "RUN_ASSURANCE_LAB"


class TrustLevel(StrEnum):
    """Ingested content is never TRUSTED on arrival (SEC-R-015)."""

    TRUSTED = "TRUSTED"
    UNTRUSTED_REVIEW_REQUIRED = "UNTRUSTED_REVIEW_REQUIRED"
    QUARANTINED_UNTRUSTED = "QUARANTINED_UNTRUSTED"


class ApprovalStatus(StrEnum):
    APPROVED = "APPROVED"
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    SUPERSEDED = "SUPERSEDED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"


class Currency(StrEnum):
    """Whether a source is still current against its own review date."""

    CURRENT = "CURRENT"
    EXPIRED = "EXPIRED"
    STALE = "STALE"
    NO_REVIEW_DATE = "NO_REVIEW_DATE"


class EvidenceState(StrEnum):
    """The five states rendered by the Audit Readiness workspace."""

    PRESENT = "PRESENT"
    MISSING = "MISSING"
    EXPIRED = "EXPIRED"
    UNAPPROVED = "UNAPPROVED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class Severity(IntEnum):
    """Ordered so that comparisons and sorting are meaningful."""

    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @property
    def label(self) -> str:
        return self.name


class ConfidenceLevel(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class AuditConclusion(StrEnum):
    """The audit-agent answer contract from the master SOP, section 11.4."""

    DEMONSTRATED = "DEMONSTRATED"
    PARTIALLY_DEMONSTRATED = "PARTIALLY_DEMONSTRATED"
    NOT_DEMONSTRATED = "NOT_DEMONSTRATED"
    NOT_APPLICABLE_WITH_EVIDENCE = "NOT_APPLICABLE_WITH_EVIDENCE"
    UNABLE_TO_DETERMINE = "UNABLE_TO_DETERMINE"


class MaturityScore(IntEnum):
    """The 0-4 scoring rubric from the master SOP, section 11.5."""

    ABSENT_OR_CONTRADICTED = 0
    CLAIM_ONLY = 1
    DOCUMENT_LOCATED = 2
    DEMONSTRATED = 3
    CORROBORATED_RESILIENT = 4


class FindingCategory(StrEnum):
    DOCUMENTATION = "DOCUMENTATION"
    VALIDATION = "VALIDATION"
    RISK = "RISK"
    SUPPLIER = "SUPPLIER"
    CHANGE = "CHANGE"
    INCIDENT = "INCIDENT"
    ACCESS = "ACCESS"
    BACKUP = "BACKUP"
    DATA_INTEGRITY = "DATA_INTEGRITY"
    TRACEABILITY = "TRACEABILITY"
    PERIODIC_REVIEW = "PERIODIC_REVIEW"
    TRAINING = "TRAINING"


class FindingStatus(StrEnum):
    OPEN = "OPEN"
    CONFLICT = "CONFLICT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    CLOSED = "CLOSED"


class ActionType(StrEnum):
    """C3 Action Gateway categories. Default is READ (ARCH-R-031)."""

    READ = "READ"
    DRAFT = "DRAFT"
    MOCK_WRITE_LOW_RISK = "MOCK_WRITE_LOW_RISK"
    GXP_RELEVANT_WRITE = "GXP_RELEVANT_WRITE"
    PROHIBITED = "PROHIBITED"


class ProposalStatus(StrEnum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CLARIFICATION_REQUESTED = "CLARIFICATION_REQUESTED"
    EXECUTED = "EXECUTED"
    BLOCKED = "BLOCKED"


class PolicyReason(StrEnum):
    ALLOWED = "ALLOWED"
    NO_MATCHING_GRANT = "NO_MATCHING_GRANT"
    ROLE_LACKS_PERMISSION = "ROLE_LACKS_PERMISSION"
    AGENT_LACKS_CAPABILITY = "AGENT_LACKS_CAPABILITY"
    TOOL_NOT_ALLOWLISTED = "TOOL_NOT_ALLOWLISTED"
    GXP_WRITE_REQUIRES_APPROVAL = "GXP_WRITE_REQUIRES_APPROVAL"
    ACTION_PROHIBITED = "ACTION_PROHIBITED"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    SOURCE_QUARANTINED = "SOURCE_QUARANTINED"


class NodeType(StrEnum):
    """Closed set of evidence-graph node types (ARCH-R-038)."""

    SYSTEM = "System"
    REQUIREMENT = "UrsRequirement"
    RISK = "Risk"
    DESIGN_ELEMENT = "DesignElement"
    CONFIG_ITEM = "ConfigItem"
    TEST_CASE = "TestCase"
    TEST_RESULT = "TestResult"
    DOCUMENT = "Document"
    DEVIATION = "Deviation"
    INCIDENT = "Incident"
    CHANGE = "Change"
    ACCESS_REVIEW = "AccessReview"
    ACCESS_ASSIGNMENT = "AccessAssignment"
    PERIODIC_EVALUATION = "PeriodicEvaluation"
    SUPPLIER_ASSESSMENT = "SupplierAssessment"
    BACKUP_RECORD = "BackupRecord"
    CAPA_ACTION = "CapaAction"
    FINDING = "Finding"
    RECOMMENDATION = "Recommendation"
    APPROVAL = "HumanApproval"
    CHECKLIST_QUESTION = "ChecklistQuestion"


class EdgeType(StrEnum):
    REQUIRES = "REQUIRES"
    SATISFIED_BY = "SATISFIED_BY"
    VERIFIED_BY = "VERIFIED_BY"
    CHANGED_BY = "CHANGED_BY"
    IMPACTS = "IMPACTS"
    OWNED_BY = "OWNED_BY"
    REVIEWED_BY = "REVIEWED_BY"
    REFERENCES = "REFERENCES"
    EVIDENCES = "EVIDENCES"
    RAISES = "RAISES"
    RECOMMENDS = "RECOMMENDS"
    APPROVED_BY = "APPROVED_BY"


class BiasControl(StrEnum):
    """Adversarial checks from the master SOP, section 11.6."""

    CONFIRMATION_BIAS = "CONFIRMATION_BIAS"
    RECENCY_STATUS_BIAS = "RECENCY_STATUS_BIAS"
    AUTHORITY_BIAS = "AUTHORITY_BIAS"
    COVERAGE_ILLUSION = "COVERAGE_ILLUSION"
    AUTOMATION_BIAS = "AUTOMATION_BIAS"
    SEVERITY_DILUTION = "SEVERITY_DILUTION"
