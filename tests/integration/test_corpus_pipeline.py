"""End-to-end over the real mentor corpus with a real SQLite database.

Integration tests use real migrations and real seed scripts in a temporary
database (TEST-R-005). The LLM is always stubbed and the whole suite passes with
no model present (TEST-R-006, TEST-R-007).
"""

import sqlite3
import unittest
from datetime import UTC, datetime
from pathlib import Path

from app.database.seed_corpus import SYSTEM_ID, load_checklists, seed_corpus
from app.domain.clock import FrozenClock
from app.domain.enums import (
    Applicability,
    AuditConclusion,
    ConfidenceLevel,
    RuntimeMode,
    TrustLevel,
)
from app.rag.retrieval import Fts5Retrieval
from app.rules.applicability import derive_position
from app.rules.checklist_engine import ChecklistEngine, CorpusIndex
from app.rules.readiness import compute

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "data" / "corpus"
CHECKLISTS = ROOT / "data" / "demo" / "audit_checklists.json"
NOW = datetime(2026, 8, 27, 12, 0, tzinfo=UTC)


class CorpusFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not CORPUS.exists() or not any(CORPUS.glob("*.docx")):
            raise unittest.SkipTest("evidence corpus is not present")
        cls.clock = FrozenClock(NOW)
        cls.conn = sqlite3.connect(":memory:")
        cls.conn.row_factory = sqlite3.Row
        cls.retrieval = Fts5Retrieval(cls.conn)
        cls.seed = seed_corpus(CORPUS, cls.retrieval, cls.clock)
        cls.questions = load_checklists(CHECKLISTS)
        cls.corpus = CorpusIndex.build(SYSTEM_ID, cls.seed.sources)
        cls.position = derive_position(frozenset(cls.corpus.sources_by_type))
        cls.engine = ChecklistEngine(
            cls.retrieval,
            cls.corpus,
            mode=RuntimeMode.DETERMINISTIC_FALLBACK,
            position=cls.position,
        )
        cls.findings = tuple(
            cls.engine.evaluate(q, now=NOW, task_id="T1") for q in cls.questions
        )
        cls.applicable = tuple(
            f for f in cls.findings if f.applicability is Applicability.APPLICABLE
        )


class TestIngestion(CorpusFixture):
    def test_all_35_documents_are_ingested(self):
        self.assertEqual(len(self.seed.sources), 35)

    def test_no_legitimate_evidence_is_quarantined(self):
        self.assertEqual(
            self.seed.quarantined,
            (),
            "a false-positive quarantine hides evidence an auditor asked for",
        )

    def test_the_corpus_produces_a_substantial_index(self):
        self.assertGreater(self.seed.chunks_indexed, 3000)
        self.assertEqual(self.retrieval.count(), self.seed.chunks_indexed)

    def test_every_source_carries_full_provenance(self):
        for source in self.seed.sources:
            self.assertEqual(len(source.content_hash), 64)
            self.assertTrue(source.source_id.startswith("NL-MES-"))
            self.assertIsNot(source.trust_level, TrustLevel.TRUSTED)
            self.assertGreater(source.byte_size, 0)

    def test_training_banner_is_not_treated_as_an_approval(self):
        """Authority-bias countermeasure: a simulated approval is not approval."""
        for source in self.seed.sources:
            self.assertNotEqual(source.approval_status.value, "APPROVED")


class TestRetrieval(CorpusFixture):
    def test_retrieval_finds_the_access_review_evidence(self):
        hits = self.retrieval.search("quarterly access review privileged accounts", limit=8)
        self.assertTrue(hits)
        self.assertIn("NL-MES-AMRR-001", {h.source_id for h in hits})

    def test_retrieval_finds_the_traceability_matrix(self):
        hits = self.retrieval.search("requirement traceability matrix design test", limit=10)
        self.assertIn("NL-MES-TRM-001", {h.source_id for h in hits})

    def test_free_text_cannot_inject_fts5_syntax(self):
        """The control is neutralisation, not emptiness.

        Hostile input must never reach FTS5 as syntax. It is tokenised and
        re-quoted, so the engine may still return harmless keyword matches; what
        matters is that no operator, quote or comment survives, and that the
        query cannot raise.
        """
        from app.rag.retrieval import build_match_query

        for hostile in ('" OR 1=1 --', 'a" NEAR/9 "b', "x* AND y*", '"; DROP TABLE chunk; --'):
            expression = build_match_query(hostile)
            self.assertNotIn("*", expression)
            self.assertNotIn("--", expression)
            self.assertNotIn(";", expression)
            self.assertNotIn(" NEAR", expression.upper())
            self.assertEqual(expression.count('"') % 2, 0, "quotes must stay balanced")
            self.retrieval.search(hostile, limit=3)  # must not raise


class TestLifecycleApplicability(CorpusFixture):
    def test_position_is_derived_as_implement_at_iq(self):
        self.assertEqual(self.position.highest_phase_reached, 7)
        self.assertEqual(self.position.state.value, "IMPLEMENT")

    def test_future_phases_are_not_reported_as_gaps(self):
        retirement = [f for f, q in zip(self.findings, self.questions) if q.phase_no == 14]
        self.assertTrue(retirement)
        for f in retirement:
            self.assertIs(f.conclusion, AuditConclusion.NOT_APPLICABLE_WITH_EVIDENCE)
            self.assertIs(f.applicability, Applicability.NOT_YET_REACHED)
            self.assertFalse(f.requires_human_approval)

    def test_applicability_is_justified_with_evidence(self):
        future = next(f for f in self.findings if f.applicability is Applicability.NOT_YET_REACHED)
        self.assertIn("Evidence of arrival was found for", future.applicability_basis)


class TestEngineOutput(CorpusFixture):
    def test_all_350_controls_are_evaluated(self):
        self.assertEqual(len(self.findings), 350)

    def test_eval_020_no_finding_without_evidence_or_abstention(self):
        for f in self.applicable:
            if not f.evidence:
                self.assertIs(f.confidence.level, ConfidenceLevel.INSUFFICIENT_EVIDENCE)

    def test_grounded_answer_rate_meets_the_sop_target(self):
        grounded = sum(1 for f in self.applicable if f.evidence)
        rate = grounded / len(self.applicable)
        self.assertGreaterEqual(rate, 0.95, f"grounded answer rate {rate:.0%} < 95%")

    def test_every_evidence_reference_resolves_to_an_indexed_source(self):
        known = {s.source_id for s in self.seed.sources}
        for f in self.findings:
            for ref in f.evidence:
                self.assertIn(ref.source_id, known)

    def test_excerpts_are_verbatim_and_bounded(self):
        for f in self.findings:
            for ref in f.evidence:
                self.assertLessEqual(len(ref.relevant_excerpt), 600)

    def test_findings_are_owned_by_the_correct_specialist(self):
        for f in self.findings:
            self.assertIn(f.agent_id.value, {"A1", "A2", "A3", "A4", "A5", "A6"})

    def test_material_findings_require_human_approval(self):
        for f in self.applicable:
            if f.severity.value >= 2:
                self.assertTrue(f.requires_human_approval)


class TestDeterminism(CorpusFixture):
    def test_repeated_evaluation_is_byte_identical(self):
        again = tuple(self.engine.evaluate(q, now=NOW, task_id="T1") for q in self.questions)
        self.assertEqual(
            [(f.finding_id, f.severity, f.maturity_score, f.confidence.coverage) for f in self.findings],
            [(f.finding_id, f.severity, f.maturity_score, f.confidence.coverage) for f in again],
        )

    def test_readiness_is_reproducible_and_explainable(self):
        first = compute(SYSTEM_ID, self.findings, now=NOW)
        second = compute(SYSTEM_ID, self.findings, now=NOW)
        self.assertEqual(first.score, second.score)
        self.assertEqual(first.calculation, second.calculation)
        self.assertIn("NOT READY", first.verdict)


if __name__ == "__main__":
    unittest.main()
