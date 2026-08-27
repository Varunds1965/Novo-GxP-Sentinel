#!/usr/bin/env python3
"""Rebuild the local evidence store from the corpus. Idempotent."""

from __future__ import annotations

import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

import _bootstrap  # noqa: F401

from app.database.seed_corpus import seed_corpus
from app.domain.clock import FrozenClock
from app.rag.retrieval import Fts5Retrieval

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    target = ROOT / "data" / "evidence.db"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()
    conn = sqlite3.connect(target)
    conn.row_factory = sqlite3.Row
    retrieval = Fts5Retrieval(conn)
    clock = FrozenClock(datetime(2026, 8, 27, 12, 0, tzinfo=UTC))
    result = seed_corpus(ROOT / "data" / "corpus", retrieval, clock)
    print(f"Seeded {len(result.sources)} sources and {result.chunks_indexed} chunks "
          f"into {target.name}")
    if result.quarantined:
        print(f"Quarantined: {', '.join(result.quarantined)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
