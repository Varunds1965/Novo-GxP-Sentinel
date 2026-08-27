"""Append-only, hash-chained audit trail.

This mechanism is tamper-EVIDENT. It is not immutable, not WORM, and not a
21 CFR Part 11 compliant record (SEC-R-043).
"""

from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Iterator

from app.domain.clock import ClockPort
from app.domain.hashing import ZERO_HASH, chain_hash

_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_event (
    seq                 INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id            TEXT    NOT NULL UNIQUE,
    occurred_at         TEXT    NOT NULL,
    session_id          TEXT    NOT NULL,
    user_id             TEXT    NOT NULL,
    role                TEXT    NOT NULL,
    agent_id            TEXT,
    action              TEXT    NOT NULL,
    tool                TEXT,
    target              TEXT,
    input_hash          TEXT,
    output_hash         TEXT,
    model_id            TEXT,
    prompt_version      TEXT,
    source_ids          TEXT    NOT NULL DEFAULT '',
    approval_id         TEXT,
    status              TEXT    NOT NULL,
    trace_id            TEXT    NOT NULL,
    previous_event_hash TEXT    NOT NULL,
    event_hash          TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_audit_trace ON audit_event(trace_id);
CREATE INDEX IF NOT EXISTS ix_audit_action ON audit_event(action);
"""

_HASHED_FIELDS = (
    "event_id",
    "occurred_at",
    "session_id",
    "user_id",
    "role",
    "agent_id",
    "action",
    "tool",
    "target",
    "input_hash",
    "output_hash",
    "model_id",
    "prompt_version",
    "source_ids",
    "approval_id",
    "status",
    "trace_id",
)


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_id: str
    occurred_at: datetime
    session_id: str
    user_id: str
    role: str
    action: str
    status: str
    trace_id: str
    agent_id: str | None = None
    tool: str | None = None
    target: str | None = None
    input_hash: str | None = None
    output_hash: str | None = None
    model_id: str | None = None
    prompt_version: str | None = None
    source_ids: str = ""
    approval_id: str | None = None

    def hashable(self) -> dict[str, Any]:
        raw = asdict(self)
        return {key: raw[key] for key in _HASHED_FIELDS}


@dataclass(frozen=True, slots=True)
class ChainVerification:
    verified: bool
    event_count: int
    first_divergent_seq: int | None = None
    detail: str = ""


class AuditRepository:
    """Exposes append() and read() only. No UPDATE, no DELETE (ARCH-R-034)."""

    def __init__(self, connection: sqlite3.Connection, clock: ClockPort) -> None:
        self._conn = connection
        self._clock = clock
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def _head_hash(self) -> str:
        row = self._conn.execute(
            "SELECT event_hash FROM audit_event ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        return row[0] if row else ZERO_HASH

    def append(self, event: AuditEvent) -> str:
        previous = self._head_hash()
        digest = chain_hash(event.hashable(), previous)
        payload = event.hashable()
        payload["occurred_at"] = event.occurred_at.isoformat()
        self._conn.execute(
            """
            INSERT INTO audit_event (
                event_id, occurred_at, session_id, user_id, role, agent_id,
                action, tool, target, input_hash, output_hash, model_id,
                prompt_version, source_ids, approval_id, status, trace_id,
                previous_event_hash, event_hash
            ) VALUES (
                :event_id, :occurred_at, :session_id, :user_id, :role, :agent_id,
                :action, :tool, :target, :input_hash, :output_hash, :model_id,
                :prompt_version, :source_ids, :approval_id, :status, :trace_id,
                :previous_event_hash, :event_hash
            )
            """,
            {**payload, "previous_event_hash": previous, "event_hash": digest},
        )
        self._conn.commit()
        return digest

    def count(self) -> int:
        return int(self._conn.execute("SELECT COUNT(*) FROM audit_event").fetchone()[0])

    def read(self, limit: int = 200, trace_id: str | None = None) -> list[sqlite3.Row]:
        if trace_id:
            return list(
                self._conn.execute(
                    "SELECT * FROM audit_event WHERE trace_id = ? ORDER BY seq DESC LIMIT ?",
                    (trace_id, limit),
                )
            )
        return list(
            self._conn.execute(
                "SELECT * FROM audit_event ORDER BY seq DESC LIMIT ?", (limit,)
            )
        )

    def _rows(self) -> Iterator[sqlite3.Row]:
        yield from self._conn.execute("SELECT * FROM audit_event ORDER BY seq ASC")

    def verify_chain(self) -> ChainVerification:
        previous = ZERO_HASH
        count = 0
        for row in self._rows():
            count += 1
            payload = {key: row[key] for key in _HASHED_FIELDS}
            expected = chain_hash(payload, previous)
            if expected != row["event_hash"]:
                return ChainVerification(
                    verified=False,
                    event_count=count,
                    first_divergent_seq=int(row["seq"]),
                    detail=(
                        f"Audit chain verification failed at event {row['seq']}. "
                        "This is expected only after using the Assurance Lab "
                        "tamper scenario."
                    ),
                )
            if row["previous_event_hash"] != previous:
                return ChainVerification(
                    verified=False,
                    event_count=count,
                    first_divergent_seq=int(row["seq"]),
                    detail=f"Predecessor hash mismatch at event {row['seq']}.",
                )
            previous = row["event_hash"]
        return ChainVerification(
            verified=True,
            event_count=count,
            detail=f"{count} events verified against the SHA-256 chain.",
        )
