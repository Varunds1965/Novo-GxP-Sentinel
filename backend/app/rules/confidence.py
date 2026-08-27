"""Deterministic evidence-confidence service.

The model NEVER produces a confidence value (GXP-R-013). Confidence is computed
from measurable evidence characteristics, every factor is named, and the UI
explains the classification in plain English (GXP-R-011, GXP-R-012).
"""

from __future__ import annotations

from datetime import datetime

from enum import Enum

from app.domain.enums import ApprovalStatus, ConfidenceLevel, Currency, TrustLevel
from app.domain.models import ConfidenceAssessment, EvidenceRef


class ClaimPolarity(str, Enum):
    """Confidence is confidence in the CONCLUSION, not a grade for the evidence.

    This distinction is the single most important idea in this module. If three
    independent records agree that an access review is overdue and remediation
    is still Open, we can be highly confident in that GAP even though every
    cited record is a draft: draft, expired and missing evidence are all
    *consistent with* the gap being real.

    The reverse claim is far harder. Asserting that a control demonstrably
    operates requires approved, current, corroborated execution evidence, so a
    CONFORMANCE claim is held to strict ceilings. Applying one symmetric formula
    to both directions is how assurance tools end up reporting high confidence
    in conclusions drawn from expired paperwork.
    """

    GAP = "GAP"
    CONFORMANCE = "CONFORMANCE"

# Factor weights. Published here and in docs/DESIGN_SPECIFICATION.md so that an
# auditor can reproduce any classification by hand.
W_DIRECT_EVIDENCE = 0.30
W_CORROBORATION = 0.20
W_APPROVAL = 0.20
W_FRESHNESS = 0.15
W_TRUST = 0.10
W_CONSISTENCY = 0.05

P_MISSING_REQUIRED = 0.35
P_CONTRADICTION = 0.30
P_QUARANTINE = 0.50

T_HIGH = 0.75
T_MEDIUM = 0.50
T_LOW = 0.20

# Ceilings for CONFORMANCE claims. Verification is a one-way ratchet downward
# (AGENT-R-023), so these can only reduce a level, never raise one.
CEILING_EXPIRED_SOURCE = ConfidenceLevel.MEDIUM
CEILING_NO_APPROVED_SOURCE = ConfidenceLevel.LOW
CEILING_NO_EXECUTION_EVIDENCE = ConfidenceLevel.MEDIUM

# A gap asserted from a single record is an observation, not a triangulated
# finding. The master SOP requires cross-record reconciliation before a
# conclusion is treated as reliable, so single-source gaps cap at MEDIUM.
CEILING_SINGLE_SOURCE_GAP = ConfidenceLevel.MEDIUM

_ORDER = (
    ConfidenceLevel.INSUFFICIENT_EVIDENCE,
    ConfidenceLevel.LOW,
    ConfidenceLevel.MEDIUM,
    ConfidenceLevel.HIGH,
)


def _cap(level: ConfidenceLevel, ceiling: ConfidenceLevel) -> ConfidenceLevel:
    return level if _ORDER.index(level) <= _ORDER.index(ceiling) else ceiling


def assess(
    evidence: tuple[EvidenceRef, ...],
    *,
    now: datetime,
    polarity: ClaimPolarity = ClaimPolarity.CONFORMANCE,
    required_evidence_count: int = 1,
    contradictions: int = 0,
    missing_required: tuple[str, ...] = (),
    execution_evidence: bool = False,
) -> ConfidenceAssessment:
    """Classify confidence as HIGH, MEDIUM, LOW or INSUFFICIENT_EVIDENCE."""
    if not evidence:
        return ConfidenceAssessment(
            level=ConfidenceLevel.INSUFFICIENT_EVIDENCE,
            coverage=0.0,
            basis="No evidence resolved in the local store for this control question.",
            factors={},
            uncertainty=(
                "Insufficient evidence to conclude: "
                + (", ".join(missing_required) if missing_required else "no source located")
            ),
        )

    factors: dict[str, float] = {}
    score = 0.0

    factors["direct_evidence"] = W_DIRECT_EVIDENCE
    score += W_DIRECT_EVIDENCE

    independent = len({ref.source_id for ref in evidence})
    corroboration = W_CORROBORATION * min(1.0, (independent - 1) / 2.0)
    factors["independent_sources"] = round(corroboration, 4)
    score += corroboration

    approved = sum(1 for r in evidence if r.approval_status is ApprovalStatus.APPROVED)
    is_gap = polarity is ClaimPolarity.GAP
    if is_gap:
        # An unapproved source does not weaken the claim that something is
        # unapproved. Award the factor on the strength of citation instead.
        approval = W_APPROVAL
        factors["approval_status_not_load_bearing"] = W_APPROVAL
    else:
        approval = W_APPROVAL * (approved / len(evidence))
        factors["approval_status"] = round(approval, 4)
    score += approval

    def currency_of(ref: EvidenceRef) -> Currency:
        if ref.review_date is None:
            return Currency.NO_REVIEW_DATE
        return Currency.EXPIRED if ref.review_date < now else Currency.CURRENT

    current = sum(1 for r in evidence if currency_of(r) is Currency.CURRENT)
    expired = sum(1 for r in evidence if currency_of(r) is Currency.EXPIRED)
    if is_gap:
        freshness = W_FRESHNESS
        factors["freshness_not_load_bearing"] = W_FRESHNESS
    else:
        freshness = W_FRESHNESS * (current / len(evidence))
        factors["freshness"] = round(freshness, 4)
    score += freshness

    trusted = sum(
        1 for r in evidence if r.trust_level is not TrustLevel.QUARANTINED_UNTRUSTED
    )
    trust = W_TRUST * (trusted / len(evidence))
    factors["source_trust"] = round(trust, 4)
    score += trust

    if contradictions == 0:
        factors["consistency"] = W_CONSISTENCY
        score += W_CONSISTENCY
    else:
        penalty = P_CONTRADICTION * min(1.0, contradictions / 2.0)
        factors["contradictions"] = -round(penalty, 4)
        score -= penalty

    if missing_required and not is_gap:
        penalty = P_MISSING_REQUIRED * min(
            1.0, len(missing_required) / max(1, required_evidence_count)
        )
        factors["missing_required_evidence"] = -round(penalty, 4)
        score -= penalty
    elif missing_required:
        factors["absence_corroborates_gap"] = 0.0

    if any(r.trust_level is TrustLevel.QUARANTINED_UNTRUSTED for r in evidence):
        factors["quarantined_source"] = -P_QUARANTINE
        score -= P_QUARANTINE

    coverage = max(0.0, min(1.0, score))

    if coverage >= T_HIGH:
        level = ConfidenceLevel.HIGH
    elif coverage >= T_MEDIUM:
        level = ConfidenceLevel.MEDIUM
    elif coverage >= T_LOW:
        level = ConfidenceLevel.LOW
    else:
        level = ConfidenceLevel.INSUFFICIENT_EVIDENCE

    ceilings: list[str] = []
    if polarity is ClaimPolarity.GAP and independent < 2:
        capped = _cap(level, CEILING_SINGLE_SOURCE_GAP)
        if capped is not level:
            ceilings.append(
                f"capped at {CEILING_SINGLE_SOURCE_GAP.value} because the gap is "
                "asserted from a single source and is not yet triangulated"
            )
        level = capped
    if polarity is ClaimPolarity.CONFORMANCE:
        if expired:
            capped = _cap(level, CEILING_EXPIRED_SOURCE)
            if capped is not level:
                ceilings.append(
                    f"capped at {CEILING_EXPIRED_SOURCE.value} because "
                    f"{expired} cited source(s) passed their review date"
                )
            level = capped
        if approved == 0:
            capped = _cap(level, CEILING_NO_APPROVED_SOURCE)
            if capped is not level:
                ceilings.append(
                    f"capped at {CEILING_NO_APPROVED_SOURCE.value} because no cited "
                    "source carries an approved status"
                )
            level = capped
        if not execution_evidence:
            capped = _cap(level, CEILING_NO_EXECUTION_EVIDENCE)
            if capped is not level:
                ceilings.append(
                    f"capped at {CEILING_NO_EXECUTION_EVIDENCE.value} because no "
                    "executed evidence corroborates the approved narrative"
                )
            level = capped
    if ceilings:
        factors["ceilings_applied"] = float(len(ceilings))

    parts = [f"{len(evidence)} evidence reference(s) from {independent} independent source(s)"]
    if approved:
        parts.append(f"{approved} approved")
    else:
        parts.append("none carrying an approved status")
    if current:
        parts.append(f"{current} current against their review date")
    if contradictions:
        parts.append(f"{contradictions} contradiction(s) detected")
    if missing_required:
        parts.append(f"missing: {', '.join(missing_required[:3])}")

    uncertainty_parts: list[str] = []
    if approved < len(evidence):
        uncertainty_parts.append(
            "some cited sources are draft or unapproved, so they evidence intent rather than execution"
        )
    if missing_required:
        uncertainty_parts.append(f"required evidence absent: {', '.join(missing_required[:4])}")
    if contradictions:
        uncertainty_parts.append("independent records disagree and were not reconciled")
    if not uncertainty_parts:
        uncertainty_parts.append("no material uncertainty identified within the indexed corpus")

    basis_text = "; ".join(parts) + f" -> coverage {coverage:.0%}"
    basis_text += f" [claim polarity: {polarity.value}]"
    if ceilings:
        basis_text += "; " + "; ".join(ceilings)

    return ConfidenceAssessment(
        level=level,
        coverage=round(coverage, 4),
        basis=basis_text,
        factors=factors,
        uncertainty="; ".join(uncertainty_parts),
    )
