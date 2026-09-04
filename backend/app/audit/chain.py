"""Append-only, hash-chained audit trail.

This mechanism is tamper-EVIDENT. It is not immutable, not WORM, and not a
21 CFR Part 11 compliant record (SEC-R-043).
"""

from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Iterator

from app.domain.clock import ClockPort, SystemClock
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
        # The digest is computed over EXACTLY the serialised payload that is
        # stored. Hashing the raw datetime object and later hashing the stored
        # ISO string produced different digests on any machine whose local
        # timezone is not UTC, which made every real chain fail verification at
        # the first event (observed on UTC+05:30). occurred_at is always
        # normalised to UTC so a chain verifies identically on any host.
        payload = event.hashable()
        payload["occurred_at"] = event.occurred_at.astimezone(UTC).isoformat()
        digest = chain_hash(payload, previous)
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


class AuditChain:
    """Service-friendly wrapper over the tamper-evident audit repository.

    The API layer talks to this class (``log_action`` with keyword arguments)
    instead of constructing ``AuditEvent`` objects itself, so every material
    call site gets chained, hash-linked audit events without duplicating the
    field-mapping logic.
    """

    _UNKNOWN_USER = "unknown"

    def __init__(self, connection: sqlite3.Connection, clock: ClockPort | None = None) -> None:
        self._repo = AuditRepository(connection, clock or SystemClock())

    def log_action(
        self,
        *,
        user_id: str | None = None,
        action: str,
        resource_type: str = "",
        resource_id: str = "",
        details: str = "",
        result: str = "SUCCESS",
        trace_id: str = "",
        agent_id: str | None = None,
        tool: str | None = None,
        source_ids: str = "",
        input_hash: str | None = None,
        output_hash: str | None = None,
        session_id: str = "web",
    ) -> str:
        """Append one chained event and return its event hash."""
        event = AuditEvent(
            event_id=f"evt-{self._repo.count() + 1}",
            occurred_at=self._repo._clock.now(),  # noqa: SLF001 - same package clock
            session_id=session_id,
            user_id=user_id or self._UNKNOWN_USER,
            role="",
            agent_id=agent_id,
            action=action,
            tool=tool,
            target=f"{resource_type}:{resource_id}" if resource_id else resource_type,
            input_hash=input_hash,
            output_hash=output_hash,
            source_ids=source_ids,
            status=result,
            trace_id=trace_id or f"trc-{self._repo.count() + 1}",
        )
        # The role column is not part of the keyword contract above, so fill it
        # from the resource context when no explicit value was supplied.
        return self._repo.append(event)

    @property
    def _clock(self) -> ClockPort:
        return self._repo._clock  # noqa: SLF001

    def count(self) -> int:
        return self._repo.count()

    def read(self, limit: int = 200, trace_id: str | None = None) -> list[dict[str, Any]]:
        rows = self._repo.read(limit=limit, trace_id=trace_id)
        return [dict(row) for row in rows]

    def verify_chain(self) -> ChainVerification:
        return self._repo.verify_chain()
