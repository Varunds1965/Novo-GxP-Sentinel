# GxP Sentinel - Local Edition

> **PROTOTYPE - SYNTHETIC DATA - NOT VALIDATED FOR PRODUCTION GxP USE**

An evidence-first, zero-cloud, multi-agent GxP assurance prototype. It answers
auditor questions with traceable evidence, detects control gaps deterministically,
requires a human for every consequential action, and keeps working when the local
language model does not.

It makes **no** outbound network call at runtime, requires **no** API key, and the
assurance core installs **nothing**.

## Quickstart

```bash
python3 scripts/offline_self_test.py     # prove the offline guarantee
python3 scripts/run_assessment.py        # assess the evidence package
python3 -m unittest discover -s tests -p 'test_*.py' -t .
```

Windows users double-click `RUN_OFFLINE_SELF_TEST.bat` then `START_GXP_SENTINEL.bat`.
There is nothing to install and no configuration to edit.

## What it does, verified

Against the supplied MES PAS-X evidence package, on a frozen assessment date of
27 August 2026:

| Measure | Result |
|---|---|
| Documents ingested, hashed, scanned and indexed | 35 |
| Searchable evidence chunks (SQLite FTS5) | 4,603 |
| Legitimate evidence wrongly quarantined | 0 |
| Audit controls evaluated | 350 of 350 |
| Assessable at the system's current lifecycle phase | 175 |
| Correctly reported as not-yet-applicable | 175 |
| Grounded answer rate | 100% |
| Material findings requiring a human decision | 169 |
| Prototype readiness indicator | 29/100, NOT READY FOR SIMULATED INSPECTION |
| Full sweep runtime | 2.7 s |
| Tests | 88 passing, no model and no packages present |

## Architecture in one screen

```
                 USER (browser)  ->  127.0.0.1:8765
                            |
     API (DTOs only)  ->  SERVICES (authz, transactions)
                            |
   A0 SUPERVISOR  ->  A1 A2 A3 A4 A5 A6 A7  (one shared local model)
                            |
   C1 EVIDENCE VERIFIER  ->  C2 POLICY GATEWAY  ->  C3 ACTION GATEWAY
                            |
                     HUMAN APPROVAL
                            |
   REPOSITORIES  ->  SQLite: evidence | audit | config | roles  + FTS5
                            |
   DETERMINISTIC RULES ENGINE  |  EVIDENCE GRAPH  |  HASH-CHAINED AUDIT
```

Seven logical specialist agents share **one** local llama.cpp model. They differ
only by prompt, tools, permissions, deterministic modules, memory scope and
output schema. The model interprets and summarises; it never decides a finding,
a severity, a confidence level, a permission or an approval.

## The two runtime modes

| Mode | Trigger | Behaviour |
|---|---|---|
| `LOCAL_AI` | the bundled model answers on loopback | full pipeline, narrative prose generated locally |
| `DETERMINISTIC_FALLBACK` | model absent or unhealthy | every feature works, narratives rendered from templates, clearly labelled |

Findings, severities, evidence references and confidence levels are **identical**
in both modes. Only the prose differs, and the interface never presents template
text as model output or the reverse.

## Documentation

| Document | Purpose |
|---|---|
| `docs/AI_PROJECT_CONSTITUTION.md` | the binding engineering charter, 260 numbered rules |
| `docs/MASTER_RESEARCH_REFERENCE.md` | every supplied source synthesised into one reference |
| `docs/ADR/0001-zero-dependency-core.md` | why the core installs nothing |
| `AGENTS.md` | binding instructions for AI contributors |

## Honest limits

This is not a validated computerised system. It makes no compliance claim about
itself and no compliance determination about anything else. The audit trail is
tamper-**evident**, not immutable and not a Part 11 record. Approvals are
prototype human approvals, not electronic signatures. Roles are simulated. OCR,
image-only PDFs and DOCX images are out of scope. See
`docs/KNOWN_LIMITATIONS.md`.

## Licence

MIT. See `LICENSE`.
