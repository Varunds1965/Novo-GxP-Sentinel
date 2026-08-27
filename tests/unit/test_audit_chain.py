"""SEC-R-040 to SEC-R-044, EVAL-015 and EVAL-016."""

import sqlite3
import unittest
from datetime import UTC, datetime

from app.audit.chain import AuditEvent, AuditRepository
from app.domain.clock import FrozenClock


class TestAuditChain(unittest.TestCase):
    def setUp(self):
        self.clock = FrozenClock(datetime(2026, 8, 27, tzinfo=UTC))
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.repo = AuditRepository(self.conn, self.clock)

    def _append(self, n=5):
        for i in range(n):
            self.repo.append(
                AuditEvent(
                    event_id=f"ev{i}",
                    occurred_at=self.clock.now(),
                    session_id="s1",
                    user_id="u1",
                    role="SYSTEM_OWNER",
                    action="READ_FINDINGS",
                    status="OK",
                    trace_id="trc_1",
                )
            )

    def test_eval_015_clean_chain_verifies(self):
        self._append()
        result = self.repo.verify_chain()
        self.assertTrue(result.verified)
        self.assertEqual(result.event_count, 5)

    def test_eval_016_tampering_breaks_verification(self):
        self._append()
        self.conn.execute("UPDATE audit_event SET status='TAMPERED' WHERE seq=3")
        self.conn.commit()
        result = self.repo.verify_chain()
        self.assertFalse(result.verified)
        self.assertEqual(result.first_divergent_seq, 3)

    def test_deletion_breaks_verification(self):
        self._append()
        self.conn.execute("DELETE FROM audit_event WHERE seq=3")
        self.conn.commit()
        self.assertFalse(self.repo.verify_chain().verified)

    def test_empty_chain_verifies_trivially(self):
        self.assertTrue(self.repo.verify_chain().verified)

    def test_genesis_event_links_to_zero_hash(self):
        self._append(1)
        row = self.conn.execute("SELECT previous_event_hash FROM audit_event").fetchone()
        self.assertEqual(row[0], "0" * 64)

    def test_events_are_retrievable_by_trace(self):
        self._append(3)
        self.assertEqual(len(self.repo.read(trace_id="trc_1")), 3)
        self.assertEqual(len(self.repo.read(trace_id="absent")), 0)

    def test_repository_exposes_no_mutation_methods(self):
        for banned in ("update", "delete", "remove", "purge"):
            self.assertFalse(
                any(banned in name for name in dir(self.repo) if not name.startswith("_")),
                f"audit repository must not expose a {banned} operation",
            )


if __name__ == "__main__":
    unittest.main()
