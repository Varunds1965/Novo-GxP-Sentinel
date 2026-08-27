#!/usr/bin/env python3
"""Evaluate every audit control against the local evidence store.

Runs with zero installed packages and zero network access.
"""

from __future__ import annotations

import sqlite3
import sys
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import _bootstrap  # noqa: F401

from app.database.seed_corpus import SYSTEM_ID, load_checklists, seed_corpus
from app.domain.clock import FrozenClock
from app.domain.enums import Applicability, MaturityScore, Severity
from app.rag.retrieval import Fts5Retrieval
from app.rules.applicability import PHASE_NAMES, derive_position
from app.rules.checklist_engine import ChecklistEngine, CorpusIndex
from app.rules.readiness import compute

ROOT = Path(__file__).resolve().parents[1]
ASSESSMENT_DATE = datetime(2026, 8, 27, 12, 0, tzinfo=UTC)
BANNER = "PROTOTYPE  -  SYNTHETIC DATA  -  NOT VALIDATED FOR PRODUCTION GxP USE"


def main() -> int:
    print("=" * 78)
    print(BANNER.center(78))
    print("=" * 78)

    clock = FrozenClock(ASSESSMENT_DATE)
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    retrieval = Fts5Retrieval(conn)

    started = time.time()
    seed = seed_corpus(ROOT / "data" / "corpus", retrieval, clock)
    questions = load_checklists(ROOT / "data" / "demo" / "audit_checklists.json")
    corpus = CorpusIndex.build(SYSTEM_ID, seed.sources)
    position = derive_position(frozenset(corpus.sources_by_type))
    engine = ChecklistEngine(retrieval, corpus, mode=engine_mode(), position=position)
    findings = tuple(engine.evaluate(q, now=clock.now(), task_id="ASSESS-1") for q in questions)
    elapsed = time.time() - started

    applicable = tuple(f for f in findings if f.applicability is Applicability.APPLICABLE)
    indicator = compute(SYSTEM_ID, findings, now=clock.now())

    print(f"\nSystem            {SYSTEM_ID}  ({position.state.value})")
    print(f"Lifecycle position highest phase reached: {position.highest_phase_reached} "
          f"- {PHASE_NAMES[position.highest_phase_reached]}")
    print(f"Evidence store    {len(seed.sources)} sources, {seed.chunks_indexed} indexed chunks, "
          f"{len(seed.quarantined)} quarantined")
    print(f"Controls          {len(findings)} supplied, {len(applicable)} assessable, "
          f"{len(findings) - len(applicable)} not yet applicable")
    print(f"Elapsed           {elapsed:.1f}s")

    grounded = sum(1 for f in applicable if f.evidence)
    print(f"\nGrounded answer rate  {grounded}/{len(applicable)} = "
          f"{100 * grounded / max(1, len(applicable)):.0f}%")
    print(f"Correct abstentions   {len(applicable) - grounded}")
    print("Maturity              "
          + ", ".join(f"{MaturityScore(k).name}={v}"
                      for k, v in sorted(Counter(f.maturity_score for f in applicable).items())))
    print("Severity              "
          + ", ".join(f"{Severity(k).name}={v}"
                      for k, v in sorted(Counter(f.severity for f in applicable).items(), reverse=True)))
    print("Conclusion            "
          + ", ".join(f"{k}={v}" for k, v in Counter(f.conclusion.value for f in applicable).items()))

    print(f"\n{'-' * 78}")
    print(f"PROTOTYPE READINESS INDICATOR   {indicator.score}/100    {indicator.verdict}")
    print(f"{indicator.open_findings} open deterministic findings - "
          f"{indicator.critical_findings} critical")
    print(f"{indicator.disclaimer}")
    print(f"{'-' * 78}")
    for dimension in indicator.dimensions:
        bar = "#" * (dimension.percentage // 4)
        print(f"  {dimension.label:26} {dimension.percentage:3d}%  {bar:25} {dimension.caption}")

    print("\nView calculation")
    for key in ("controls_supplied", "controls_not_yet_applicable", "controls_evaluated",
                "weighted_subtotal", "critical_findings", "critical_rate",
                "ceiling_applied", "final_score"):
        if key in indicator.calculation:
            print(f"  {key:30} {indicator.calculation[key]}")

    print("\nPhase readiness")
    for phase in sorted(PHASE_NAMES):
        subset = tuple(f for f, q in zip(findings, questions) if q.phase_no == phase)
        if not subset:
            continue
        if all(f.applicability is not Applicability.APPLICABLE for f in subset):
            print(f"  {phase:2d} {PHASE_NAMES[phase]:44}   n/a  not yet reached")
            continue
        sub = compute(SYSTEM_ID, subset, now=clock.now())
        print(f"  {phase:2d} {PHASE_NAMES[phase]:44} {sub.score:3d}/100  "
              f"critical={sub.critical_findings}")
    return 0


def engine_mode():
    from app.domain.enums import RuntimeMode

    return RuntimeMode.DETERMINISTIC_FALLBACK


if __name__ == "__main__":
    sys.exit(main())
