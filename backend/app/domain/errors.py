"""One exception hierarchy for the whole application (ERR-R-001)."""

from __future__ import annotations


class GxpSentinelError(Exception):
    """Root of every error raised by this application."""

    code = "GXPS_ERROR"
    http_status = 500

    def __init__(
        self,
        human_message: str,
        *,
        remediation: str = "",
        technical_detail: str = "",
    ) -> None:
        super().__init__(human_message)
        self.human_message = human_message
        self.remediation = remediation
        self.technical_detail = technical_detail

    def to_problem_detail(self, instance: str, trace_id: str) -> dict[str, object]:
        return {
            "type": f"https://gxp-sentinel.local/errors/{self.code.lower().replace('_', '-')}",
            "title": self.human_message,
            "status": self.http_status,
            "code": self.code,
            "instance": instance,
            "trace_id": trace_id,
            "remediation": self.remediation,
        }


class ConfigurationError(GxpSentinelError):
    code = "CONFIGURATION_ERROR"


class ValidationError(GxpSentinelError):
    code = "VALIDATION_ERROR"
    http_status = 400


class NotFoundError(GxpSentinelError):
    code = "NOT_FOUND"
    http_status = 404


class AuthorizationError(GxpSentinelError):
    code = "FORBIDDEN"
    http_status = 403


class EvidenceError(GxpSentinelError):
    code = "EVIDENCE_ERROR"
    http_status = 409


class EvidenceNotFoundError(EvidenceError):
    code = "EVIDENCE_NOT_FOUND"


class EvidenceStaleError(EvidenceError):
    code = "EVIDENCE_STALE"


class EvidenceConflictError(EvidenceError):
    code = "EVIDENCE_CONFLICT"


class InsufficientEvidenceError(EvidenceError):
    """A domain outcome, not a failure (ERR-R-003)."""

    code = "INSUFFICIENT_EVIDENCE"
    http_status = 200


class IngestionError(GxpSentinelError):
    code = "INGESTION_ERROR"
    http_status = 422


class UnsupportedFormatError(IngestionError):
    code = "UNSUPPORTED_FORMAT"
    http_status = 415


class FileTooLargeError(IngestionError):
    code = "FILE_TOO_LARGE"
    http_status = 413


class ExtractionError(IngestionError):
    code = "EXTRACTION_FAILED"


class QuarantinedError(IngestionError):
    code = "QUARANTINED"


class AgentError(GxpSentinelError):
    code = "AGENT_ERROR"


class AgentTimeoutError(AgentError):
    code = "AGENT_TIMEOUT"


class BudgetExceededError(AgentError):
    code = "BUDGET_EXCEEDED"
    http_status = 429


class ToolNotAllowedError(AgentError):
    code = "TOOL_NOT_ALLOWED"
    http_status = 403


class ActionError(GxpSentinelError):
    code = "ACTION_ERROR"


class ApprovalRequiredError(ActionError):
    code = "APPROVAL_REQUIRED"
    http_status = 403


class PreconditionFailedError(ActionError):
    code = "PRECONDITION_FAILED"
    http_status = 409


class ProposalMutatedError(ActionError):
    code = "PROPOSAL_MUTATED"
    http_status = 409


class AuditChainBrokenError(GxpSentinelError):
    code = "AUDIT_CHAIN_BROKEN"
