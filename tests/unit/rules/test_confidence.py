"""GXP-R-011 to GXP-R-014 and the direction-aware confidence contract."""

import unittest
from datetime import UTC, datetime, timedelta

from app.domain.enums import ApprovalStatus, ConfidenceLevel, TrustLevel
from app.domain.models import EvidenceRef
from app.rules.confidence import ClaimPolarity, assess

NOW = datetime(2026, 8, 27, tzinfo=UTC)


def ref(source_id, approval=ApprovalStatus.APPROVED, review_offset=30, trust=TrustLevel.UNTRUSTED_REVIEW_REQUIRED):
    return EvidenceRef(
        source_id=source_id,
        title=source_id,
        location="p1",
        content_hash="a" * 64,
        version="1.0",
        approval_status=approval,
        trust_level=trust,
        relevant_excerpt="verbatim excerpt",
        retrieved_at=NOW,
        review_date=NOW + timedelta(days=review_offset),
    )


class TestAbstention(unittest.TestCase):
    def test_no_evidence_is_insufficient_never_low(self):
        a = assess((), now=NOW)
        self.assertIs(a.level, ConfidenceLevel.INSUFFICIENT_EVIDENCE)
        self.assertEqual(a.coverage, 0.0)

    def test_abstention_names_what_is_missing(self):
        a = assess((), now=NOW, missing_required=("executed test evidence for URS-MES-042",))
        self.assertIn("URS-MES-042", a.uncertainty)
        self.assertIn("Insufficient evidence to conclude", a.uncertainty)


class TestConformanceIsStrict(unittest.TestCase):
    def test_expired_source_caps_at_medium(self):
        a = assess(
            (ref("D1", review_offset=-30), ref("D2", review_offset=-30), ref("D3", review_offset=-30)),
            now=NOW,
            polarity=ClaimPolarity.CONFORMANCE,
            execution_evidence=True,
        )
        self.assertIs(a.level, ConfidenceLevel.MEDIUM)
        self.assertIn("review date", a.basis)

    def test_no_approved_source_caps_at_low(self):
        a = assess(
            tuple(ref(f"D{i}", approval=ApprovalStatus.DRAFT) for i in range(3)),
            now=NOW,
            polarity=ClaimPolarity.CONFORMANCE,
            execution_evidence=True,
        )
        self.assertIs(a.level, ConfidenceLevel.LOW)

    def test_absent_execution_evidence_caps_at_medium(self):
        a = assess((ref("D1"),), now=NOW, polarity=ClaimPolarity.CONFORMANCE, execution_evidence=False)
        self.assertIs(a.level, ConfidenceLevel.MEDIUM)

    def test_approved_current_corroborated_reaches_high(self):
        a = assess(
            (ref("D1"), ref("D2"), ref("D3")),
            now=NOW,
            polarity=ClaimPolarity.CONFORMANCE,
            execution_evidence=True,
        )
        self.assertIs(a.level, ConfidenceLevel.HIGH)


class TestGapPolarity(unittest.TestCase):
    def test_draft_evidence_still_supports_a_gap_conclusion(self):
        a = assess(
            tuple(ref(f"D{i}", approval=ApprovalStatus.DRAFT) for i in range(3)),
            now=NOW,
            polarity=ClaimPolarity.GAP,
            missing_required=("executed test evidence",),
        )
        self.assertIs(a.level, ConfidenceLevel.HIGH)

    def test_single_source_gap_is_not_triangulated(self):
        a = assess((ref("D1"),), now=NOW, polarity=ClaimPolarity.GAP, missing_required=("x",))
        self.assertIs(a.level, ConfidenceLevel.MEDIUM)
        self.assertIn("triangulated", a.basis)

    def test_polarity_is_recorded_in_the_basis(self):
        a = assess((ref("D1"),), now=NOW, polarity=ClaimPolarity.GAP)
        self.assertIn("GAP", a.basis)


class TestPenalties(unittest.TestCase):
    def test_quarantined_source_is_penalised(self):
        clean = assess((ref("D1"),), now=NOW)
        dirty = assess(
            (ref("D1", trust=TrustLevel.QUARANTINED_UNTRUSTED),), now=NOW
        )
        self.assertLess(dirty.coverage, clean.coverage)

    def test_contradictions_lower_confidence_and_are_explained(self):
        a = assess((ref("D1"), ref("D2")), now=NOW, contradictions=2, execution_evidence=True)
        self.assertIn("disagree", a.uncertainty)

    def test_coverage_is_always_bounded(self):
        a = assess(tuple(ref(f"D{i}") for i in range(20)), now=NOW, execution_evidence=True)
        self.assertLessEqual(a.coverage, 1.0)
        self.assertGreaterEqual(a.coverage, 0.0)

    def test_factors_are_exposed_for_the_view_calculation_panel(self):
        a = assess((ref("D1"),), now=NOW)
        self.assertIn("direct_evidence", a.factors)


if __name__ == "__main__":
    unittest.main()
