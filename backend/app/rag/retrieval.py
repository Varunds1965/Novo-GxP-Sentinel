"""Local lexical retrieval over SQLite FTS5 with deterministic re-ranking.

No embedding model and no vector database (PRIN-R-030). BM25 from FTS5 plus a
transparent metadata re-rank is sufficient for the first prototype and is fully
explainable to an auditor, which a dense vector score is not.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass

from app.domain.enums import ApprovalStatus, TrustLevel

_SCHEMA = """
CREATE TABLE IF NOT EXISTS chunk (
    chunk_id   TEXT PRIMARY KEY,
    source_id  TEXT NOT NULL,
    ordinal    INTEGER NOT NULL,
    location   TEXT NOT NULL,
    body       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_chunk_source ON chunk(source_id);
CREATE VIRTUAL TABLE IF NOT EXISTS chunk_fts USING fts5(
    body,
    chunk_id UNINDEXED,
    source_id UNINDEXED,
    tokenize = 'porter unicode61'
);
"""

_STOPWORDS = frozenset(
    """a an the and or of to in for on with is are was were be been by as at from that this
    it its any all show me give please tell what which who whom how why when do does did
    our we you your""".split()
)

_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-_./]*")

# Deterministic re-rank weights. Documented and auditable (GXP-R-008).
_W_BM25 = 1.0
_W_APPROVED = 0.35
_W_CURRENT = 0.25
_W_TRUSTED = 0.30
_P_QUARANTINE = -10.0


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    chunk_id: str
    source_id: str
    location: str
    body: str
    bm25: float
    rerank_score: float
    rerank_basis: str


def build_match_query(question: str) -> str:
    """Build a safe FTS5 MATCH expression from free text.

    User text never reaches FTS5 verbatim; it is tokenised and re-quoted, which
    prevents both syntax errors and FTS5 operator injection.
    """
    tokens = [t.lower() for t in _TOKEN.findall(question)]
    kept = [t for t in tokens if t not in _STOPWORDS and len(t) > 2]
    if not kept:
        kept = tokens[:6]
    if not kept:
        return '""'
    seen: list[str] = []
    for token in kept:
        if token not in seen:
            seen.append(token)
    return " OR ".join(f'"{t}"' for t in seen[:24])


class Fts5Retrieval:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def index_chunks(self, chunks) -> int:
        rows = [(c.chunk_id, c.source_id, c.ordinal, c.location, c.text) for c in chunks]
        if not rows:
            return 0
        self._conn.executemany(
            "INSERT OR REPLACE INTO chunk (chunk_id, source_id, ordinal, location, body)"
            " VALUES (?, ?, ?, ?, ?)",
            rows,
        )
        self._conn.executemany(
            "INSERT INTO chunk_fts (body, chunk_id, source_id) VALUES (?, ?, ?)",
            [(r[4], r[0], r[1]) for r in rows],
        )
        self._conn.commit()
        return len(rows)

    def count(self) -> int:
        return int(self._conn.execute("SELECT COUNT(*) FROM chunk").fetchone()[0])

    def search(
        self,
        question: str,
        *,
        limit: int = 20,
        source_metadata: dict[str, tuple[ApprovalStatus, TrustLevel, bool]] | None = None,
        system_id: str | None = None,
    ) -> tuple[RetrievedChunk, ...]:
        match = build_match_query(question)
        try:
            raw = list(
                self._conn.execute(
                    """
                    SELECT c.chunk_id, c.source_id, c.location, c.body, bm25(chunk_fts) AS score
                    FROM chunk_fts
                    JOIN chunk c ON c.chunk_id = chunk_fts.chunk_id
                    WHERE chunk_fts MATCH ?
                    ORDER BY score
                    LIMIT ?
                    """,
                    (match, limit * 4),
                )
            )
        except sqlite3.OperationalError:
            return ()

        metadata = source_metadata or {}
        results: list[RetrievedChunk] = []
        for chunk_id, source_id, location, body, score in raw:
            # FTS5 bm25() returns a negative number where lower is better.
            base = -float(score) * _W_BM25
            bonus = 0.0
            basis: list[str] = [f"bm25={-float(score):.3f}"]
            approval, trust, current = metadata.get(
                source_id, (ApprovalStatus.UNKNOWN, TrustLevel.UNTRUSTED_REVIEW_REQUIRED, False)
            )
            if trust is TrustLevel.QUARANTINED_UNTRUSTED:
                continue  # quarantined content is unreachable by retrieval
            if approval is ApprovalStatus.APPROVED:
                bonus += _W_APPROVED
                basis.append(f"approved+{_W_APPROVED}")
            if current:
                bonus += _W_CURRENT
                basis.append(f"current+{_W_CURRENT}")
            if trust is TrustLevel.TRUSTED:
                bonus += _W_TRUSTED
                basis.append(f"trusted+{_W_TRUSTED}")
            results.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    source_id=source_id,
                    location=location,
                    body=body,
                    bm25=-float(score),
                    rerank_score=base + bonus,
                    rerank_basis=", ".join(basis),
                )
            )
        results.sort(key=lambda r: r.rerank_score, reverse=True)
        return tuple(results[:limit])
