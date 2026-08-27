"""UI-R-015 and GXP-R-008: the indicator must be explainable and monotonic."""

import unittest
from datetime import UTC, datetime

from app.domain.enums import (
    AgentId,
    Applicability,
    AuditConclusion,
    ConfidenceLevel,
    EvidenceState,
    FindingCategory,
    FindingStatus,
    MaturityScore,
    RuntimeMode,
    Severity,
)
from app.domain.models import AgentFinding, ConfidenceAssessment
from app.rules.readiness import compute, maturity_from_state

NOW = datetime(2026, 8, 27, tzinfo=UTC)


def finding(
    fid, category, severity, maturity, applicability=Applicability.APPLICABLE
):
    return AgentFinding(
        finding_id=fid,
        task_id="T",
        agent_id=AgentId.A2_AUDIT,
        system_id="SYS",
        category=category,
        severity=severity,
        claim="c",
        evidence=(),
        evidence_state=EvidenceState.MISSING,
        confidence=ConfidenceAssessment(
            level=ConfidenceLevel.INSUFFICIENT_EVIDENCE, coverage=0.0, basis="b"
        ),
        conclusion=AuditConclusion.NOT_DEMONSTRATED,
        maturity_score=maturity,
        recommended_action="a",
        requires_human_approval=False,
        status=FindingStatus.OPEN,
        generation_mode=RuntimeMode.DETERMINISTIC_FALLBACK,
        rule_id="R",
        applicability=applicability,
    )


class TestExplainability(unittest.TestCase):
    def test_calculation_exposes_every_input(self):
        r = compute("SYS", (finding("F1", FindingCategory.ACCESS, Severity.HIGH, MaturityScore.CLAIM_ONLY),), now=NOW)
        for key in ("weighted_subtotal", "controls_evaluated", "critical_findings", "final_score", "ceiling_applied"):
            self.assertIn(key, r.calculation)

    def test_dimension_weights_sum_to_one(self):
        r = compute("SYS", (finding("F1", FindingCategory.ACCESS, Severity.LOW, MaturityScore.DEMONSTRATED),), now=NOW)
        self.assertAlmostEqual(sum(d.weight for d in r.dimensions), 1.0, places=6)

    def test_disclaimer_is_always_present(self):
        r = compute("SYS", (), now=NOW)
        self.assertEqual(r.disclaimer, "Not a compliance certification.")


class TestScoringBehaviour(unittest.TestCase):
    def test_score_is_bounded(self):
        for sev, mat in ((Severity.CRITICAL, MaturityScore.ABSENT_OR_CONTRADICTED),
                         (Severity.INFO, MaturityScore.CORROBORATED_RESILIENT)):
            r = compute("SYS", tuple(finding(f"F{i}", FindingCategory.ACCESS, sev, mat) for i in range(20)), now=NOW)
            self.assertGreaterEqual(r.score, 0)
            self.assertLessEqual(r.score, 100)

    ALL_CATEGORIES = (
        FindingCategory.DOCUMENTATION, FindingCategory.VALIDATION,
        FindingCategory.PERIODIC_REVIEW, FindingCategory.RISK,
        FindingCategory.SUPPLIER, FindingCategory.CHANGE, FindingCategory.BACKUP,
        FindingCategory.INCIDENT, FindingCategory.ACCESS,
        FindingCategory.TRACEABILITY, FindingCategory.DATA_INTEGRITY,
        FindingCategory.TRAINING,
    )

    def _healthy_estate(self):
        return tuple(
            finding(f"G{i}", category, Severity.INFO, MaturityScore.CORROBORATED_RESILIENT)
            for i, category in enumerate(self.ALL_CATEGORIES * 5)
        )

    def test_a_healthy_estate_can_score_well(self):
        r = compute("SYS", self._healthy_estate(), now=NOW)
        self.assertGreaterEqual(r.score, 95)
        self.assertIn("READY", r.verdict)

    def test_a_single_critical_forbids_a_high_score(self):
        """One critical must cap the headline number even amid a wall of green."""
        healthy = self._healthy_estate()
        bad = finding("B", FindingCategory.ACCESS, Severity.CRITICAL, MaturityScore.ABSENT_OR_CONTRADICTED)
        clean = compute("SYS", healthy, now=NOW)
        with_critical = compute("SYS", healthy + (bad,), now=NOW)
        self.assertGreater(clean.score, with_critical.score)
        self.assertLessEqual(with_critical.score, 65)
        self.assertIn("NOT READY", with_critical.verdict)

    def test_score_never_increases_when_a_critical_is_added(self):
        base = self._healthy_estate()
        previous = compute("SYS", base, now=NOW).score
        for i in range(5):
            base = base + (
                finding(f"C{i}", FindingCategory.ACCESS, Severity.CRITICAL,
                        MaturityScore.ABSENT_OR_CONTRADICTED),
            )
            current = compute("SYS", base, now=NOW).score
            self.assertLessEqual(current, previous)
            previous = current

    def test_penalty_does_not_saturate_at_scale(self):
        """The defect that made a 350-control sweep score zero."""
        many = tuple(
            finding(f"F{i}", FindingCategory.ACCESS, Severity.HIGH, MaturityScore.DOCUMENT_LOCATED)
            for i in range(350)
        )
        r = compute("SYS", many, now=NOW)
        self.assertGreater(r.score, 0, "a maturity-2 estate must not score zero")

    def test_not_yet_applicable_controls_are_excluded_from_the_denominator(self):
        applicable = finding("A", FindingCategory.ACCESS, Severity.INFO, MaturityScore.DEMONSTRATED)
        future = finding("B", FindingCategory.ACCESS, Severity.INFO, MaturityScore.DOCUMENT_LOCATED,
                         applicability=Applicability.NOT_YET_REACHED)
        r = compute("SYS", (applicable, future), now=NOW)
        self.assertEqual(r.calculation["controls_supplied"], 2.0)
        self.assertEqual(r.calculation["controls_not_yet_applicable"], 1.0)
        self.assertEqual(r.calculation["controls_evaluated"], 1.0)


class TestMaturityRubric(unittest.TestCase):
    def test_rubric_matches_the_master_sop_levels(self):
        base = dict(evidence_found=True, approved=True, current=True,
                    execution_evidence=True, corroborated=False, contradicted=False)
        self.assertIs(maturity_from_state(**{**base, "evidence_found": False}), MaturityScore.ABSENT_OR_CONTRADICTED)
        self.assertIs(maturity_from_state(**{**base, "contradicted": True}), MaturityScore.ABSENT_OR_CONTRADICTED)
        self.assertIs(maturity_from_state(**{**base, "approved": False, "execution_evidence": False}), MaturityScore.CLAIM_ONLY)
        self.assertIs(maturity_from_state(**{**base, "current": False}), MaturityScore.DOCUMENT_LOCATED)
        self.assertIs(maturity_from_state(**base), MaturityScore.DEMONSTRATED)
        self.assertIs(maturity_from_state(**{**base, "corroborated": True}), MaturityScore.CORROBORATED_RESILIENT)


if __name__ == "__main__":
    unittest.main()
