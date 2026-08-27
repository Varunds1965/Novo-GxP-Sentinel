# ADR 0001 - The assurance core has zero runtime dependencies

- Status: Accepted
- Date: 2026-08-27
- Deciders: Technical Lead / Principal Architect

## Context

The zero-key override states that the end user is not a developer, may have no
Python or Node environment, and may be on a managed laptop where endpoint
security blocks downloads and package installation. The mentor specification
also names FastAPI, Pydantic and NetworkX as the pragmatic stack.

Those two statements are in tension. Every runtime dependency is a step that can
fail on the target machine, and a dependency failure five minutes before a
presentation is indistinguishable from a broken product.

## Decision

The **assurance core** is implemented on the Python standard library alone:
domain models, the deterministic rules engine, confidence, readiness scoring,
lifecycle applicability, the twelve-step ingestion pipeline, all seven document
extractors, FTS5 retrieval, the evidence graph, the hash-chained audit trail,
and both the Policy and Action gateways.

FastAPI, Uvicorn and Pydantic remain declared as the `api` optional extra and
are used only at the HTTP boundary. When they are absent the application still
seeds, assesses, scores, audits and exports through `scripts/` and the launcher.

Concretely:

| Specification suggestion | Implementation | Why |
|---|---|---|
| Pydantic models | frozen `dataclasses` with `__post_init__` validators | identical invariants, no install |
| NetworkX graph | a small typed adjacency structure over closed node/edge enums | one file replaces a dependency for the queries actually needed |
| PyYAML configs | JSON configs under `config/` | stdlib parser; YAML supplied only thresholds, and JSON supplies them equally well |
| `defusedxml` | pre-parse refusal of DOCTYPE, ENTITY and external references | closes XXE and billion-laughs without trusting parser internals, and is directly testable |
| `python-docx`, `openpyxl`, `pypdf` | `zipfile` + `xml.etree` + `zlib` extractors | verified against all 35 real corpus documents |

## Consequences

Positive: the product runs on any machine with Python 3.12 and nothing else;
supply-chain surface for the safety-critical code is zero; CI needs no lockfile
resolution to prove the offline claim; the whole suite runs with no model and no
packages present, which is the standing proof of `DETERMINISTIC_FALLBACK` parity.

Negative: three extractors are narrower than their library equivalents. PDF text
extraction handles uncompressed and Flate streams but not every exotic filter,
and image-only PDFs are explicitly out of scope pending OCR. These limits are
recorded in `docs/KNOWN_LIMITATIONS.md` and surfaced in the UI at the point of
upload rather than hidden.

Reversible: the extractor and graph ports are Protocols. Swapping in
`python-docx` or NetworkX later is an adapter change behind an unchanged
interface, not a rewrite.
