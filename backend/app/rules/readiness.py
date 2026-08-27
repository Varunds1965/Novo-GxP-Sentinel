"""Explainable readiness indicator.

Never called a compliance certification. Every input, weight and arithmetic
step is exposed through `calculation` so the UI's "View calculation" panel can
reproduce the number exactly (UI-R-015).
"""

from __future__ import annotations

from datetime import datetime

from app.domain.enums import Applicability, FindingCategory, MaturityScore, Severity
from app.domain.models import AgentFinding, ReadinessDimension, ReadinessIndicator

# Dimension weights, from config/readiness_rules.json. Sum to 1.0.
DIMENSIONS: tuple[tuple[str, str, str, float, tuple[FindingCategory, ...]], ...] = (
    ("compliance", "Compliance & readiness", "Control evidence", 0.25,
     (FindingCategory.DOCUMENTATION, FindingCategory.VALIDATION, FindingCategory.PERIODIC_REVIEW)),
    ("risk", "Risk posture", "Demo rubric", 0.20,
     (FindingCategory.RISK, FindingCategory.SUPPLIER)),
    ("operations", "Operations", "Service evidence", 0.15,
     (FindingCategory.CHANGE, FindingCategory.BACKUP)),
    ("incidents", "Incidents", "Open events", 0.15,
     (FindingCategory.INCIDENT,)),
    ("access", "Access", "Review status", 0.15,
     (FindingCategory.ACCESS,)),
    ("documentation", "Documentation", "Indexed sources", 0.10,
     (FindingCategory.TRACEABILITY, FindingCategory.DATA_INTEGRITY, FindingCategory.TRAINING)),
)

# A critical finding cannot be averaged away by a wall of green (GXP-R-009).
# The penalty is expressed as a RATE, not a count: an absolute per-finding
# penalty is stable across a hand-seeded demo of eight findings but saturates to
# zero across a full 350-control sweep, which would make the indicator useless
# at exactly the scale that matters. Rates keep the meaning of the number
# constant whether ten or a thousand controls are evaluated.
# Severity acts as a CEILING, never as a subtraction. Severity in this engine is
# derived from maturity, so subtracting a severity penalty from a
# maturity-derived subtotal penalises the same weakness twice and drives every
# realistic corpus to zero, destroying the information the score exists to carry.
# A ceiling composes correctly: weak evidence already lowers the subtotal, and
# the presence of criticals additionally forbids a high score.
CRITICAL_CAP = 65
HIGH_CAP = 80
CRITICAL_RATE_CAP_FLOOR = 25.0

VERDICT_READY = "READY FOR SIMULATED INSPECTION"
VERDICT_QUALIFIED = "READY WITH CONTROLLED ACTIONS"
VERDICT_NOT_READY = "NOT READY FOR SIMULATED INSPECTION"


def _dimension_score(findings: tuple[AgentFinding, ...]) -> tuple[int, int]:
    """Return (percentage, evaluated_count) from maturity scores 0..4."""
    if not findings:
        return 0, 0
    total = sum(int(f.maturity_score) for f in findings)
    return round(100 * total / (4 * len(findings))), len(findings)


def compute(
    system_id: str,
    findings: tuple[AgentFinding, ...],
    *,
    now: datetime,
) -> ReadinessIndicator:
    calculation: dict[str, float] = {}
    dimensions: list[ReadinessDimension] = []
    weighted = 0.0

    # Controls for phases the system has not reached are reported but excluded
    # from the denominator; scoring them would punish a project for not yet
    # having done work it is not yet due to do.
    assessable = tuple(f for f in findings if f.applicability is Applicability.APPLICABLE)
    excluded = len(findings) - len(assessable)
    calculation["controls_supplied"] = float(len(findings))
    calculation["controls_not_yet_applicable"] = float(excluded)
    findings = assessable

    for key, label, caption, weight, categories in DIMENSIONS:
        subset = tuple(f for f in findings if f.category in categories)
        pct, count = _dimension_score(subset)
        dimensions.append(
            ReadinessDimension(
                key=key,
                label=label,
                percentage=pct,
                caption=f"{caption} ({count} checks)" if count else f"{caption} (not evaluated)",
                weight=weight,
            )
        )
        calculation[f"dim.{key}.percentage"] = float(pct)
        calculation[f"dim.{key}.weight"] = weight
        calculation[f"dim.{key}.checks"] = float(count)
        weighted += pct * weight

    calculation["weighted_subtotal"] = round(weighted, 4)

    critical = sum(1 for f in findings if f.severity is Severity.CRITICAL)
    high = sum(1 for f in findings if f.severity is Severity.HIGH)
    evaluated = max(1, len(findings))
    critical_rate = critical / evaluated
    high_rate = high / evaluated
    calculation["controls_evaluated"] = float(evaluated)
    calculation["critical_findings"] = float(critical)
    calculation["high_findings"] = float(high)
    calculation["critical_rate"] = round(critical_rate, 4)
    calculation["high_rate"] = round(high_rate, 4)

    ceiling = 100.0
    if critical:
        # A dense cluster of criticals lowers the ceiling further, down to a
        # floor, so that "one critical" and "half the estate critical" cannot
        # produce the same headline number.
        ceiling = max(
            CRITICAL_RATE_CAP_FLOOR,
            CRITICAL_CAP - (CRITICAL_CAP - CRITICAL_RATE_CAP_FLOOR) * critical_rate,
        )
        calculation["critical_ceiling"] = round(ceiling, 4)
    elif high:
        ceiling = HIGH_CAP
        calculation["high_ceiling"] = float(HIGH_CAP)

    score = min(weighted, ceiling)
    calculation["ceiling_applied"] = round(ceiling, 4)

    final = int(max(0, min(100, round(score))))
    calculation["final_score"] = float(final)

    unresolved = sum(1 for f in findings if f.severity >= Severity.MEDIUM)
    if critical or final < 50:
        verdict = VERDICT_NOT_READY
    elif final < 75:
        verdict = VERDICT_QUALIFIED
    else:
        verdict = VERDICT_READY

    return ReadinessIndicator(
        system_id=system_id,
        score=final,
        verdict=verdict,
        open_findings=unresolved,
        critical_findings=critical,
        dimensions=tuple(dimensions),
        calculation=calculation,
        computed_at=now,
    )


def maturity_from_state(
    *,
    evidence_found: bool,
    approved: bool,
    current: bool,
    execution_evidence: bool,
    corroborated: bool,
    contradicted: bool,
) -> MaturityScore:
    """Map deterministic evidence state onto the master SOP's 0-4 rubric."""
    if contradicted or not evidence_found:
        return MaturityScore.ABSENT_OR_CONTRADICTED
    if not approved and not execution_evidence:
        return MaturityScore.CLAIM_ONLY
    if not (approved and current and execution_evidence):
        return MaturityScore.DOCUMENT_LOCATED
    if corroborated:
        return MaturityScore.CORROBORATED_RESILIENT
    return MaturityScore.DEMONSTRATED
