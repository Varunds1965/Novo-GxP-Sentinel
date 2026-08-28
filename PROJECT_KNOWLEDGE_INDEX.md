# PROJECT KNOWLEDGE INDEX

**PROTOTYPE - SYNTHETIC DATA - NOT VALIDATED FOR PRODUCTION GxP USE**
*Not a compliance certification.*

This file was **0 bytes** until 2026-08-28. It now lists **only files that actually exist** in `origin/main`. Verified by directory listing, not by prior documentation.

Authoritative status record: **[`docs/FINAL_REPOSITORY_AUDIT.md`](docs/FINAL_REPOSITORY_AUDIT.md)**. Where any other document conflicts with it, the audit wins.

## Source-of-truth hierarchy

1. Mentor/company requirements → 2. Visual User Manual / prototype → 3. AI Project Constitution → 4. Company-provided evidence → 5. Research corpus → 6. Existing executable implementation → 7. Engineering judgement

## Mentor material (`MENTOR_PROVIDED`)

| File | Size |
|---|---|
| [`docs/AI_PROJECT_CONSTITUTION.md`](docs/AI_PROJECT_CONSTITUTION.md) | 157 KB - binding |
| [`docs/Codex Prototype prompt.txt`](docs/Codex%20Prototype%20prompt.txt) | 76 KB |
| `docs/GxP_Sentinel_Visual_User_Manual.pdf` | 2.4 MB - authoritative UI spec |

## Generated documentation (`GENERATED` - prior-agent output)

| File | Size |
|---|---|
| [`docs/FINAL_REPOSITORY_AUDIT.md`](docs/FINAL_REPOSITORY_AUDIT.md) | this audit |
| [`docs/MASTER_RESEARCH_REFERENCE.md`](docs/MASTER_RESEARCH_REFERENCE.md) | 63 KB - citations **not yet reconciled** |
| [`docs/M0_M2_HANDOFF_REVIEW.md`](docs/M0_M2_HANDOFF_REVIEW.md) | 28 KB |
| [`docs/M3_SYSTEM_DESIGN.md`](docs/M3_SYSTEM_DESIGN.md) | 15 KB |
| [`docs/PROGRESS_REPORT_M0_M3.md`](docs/PROGRESS_REPORT_M0_M3.md) | 13 KB |
| [`docs/ADR/0001-zero-dependency-core.md`](docs/ADR/0001-zero-dependency-core.md) | 3 KB |
| [`AGENTS.md`](AGENTS.md) | 3 KB - `DOCUMENTATION_ONLY`, describes agents with no implementing code |
| [`README.md`](README.md) | 4 KB - **needs rewrite** to match reality |

## Documents referenced by earlier reports that DO NOT EXIST

`docs/FINAL_PROJECT_STATUS.md` · `docs/TEST_VERIFICATION.md` · `docs/M4_M10_IMPLEMENTATION_STATUS.md` · `docs/TRACEABILITY_MATRIX.md` · `docs/CONSTITUTION_TRACEABILITY.md` · `docs/SOURCE_HIERARCHY.md` · `docs/ARCHITECTURE.md` · `docs/API_SPECIFICATION.md` · `docs/DATABASE_SCHEMA.md` · `docs/SECURITY_MODEL.md` · `docs/THREAT_MODEL.md` · `docs/AGENT_SPECIFICATION.md` · `docs/KNOWN_LIMITATIONS.md` · `docs/DEMO_GUIDE.md` · `docs/INSTALLATION.md` · `docs/WINDOWS_VERIFICATION.md` · `docs/RELEASE_READINESS.md` · `docs/RELEASE_MANIFEST.md`

Do not cite these until they are written.

## Backend code that exists

| Area | Files | Status |
|---|---|---|
| `backend/app/domain/` | `models.py`, `enums.py`, `errors.py`, `hashing.py`, `clock.py` | `IMPLEMENTED_NOT_EXECUTED` |
| `backend/app/rules/` | `checklist_engine.py`, `confidence.py`, `readiness.py`, `applicability.py` | `IMPLEMENTED_NOT_EXECUTED` |
| `backend/app/rag/` | `ingestion.py`, `retrieval.py`, `extractors/` | `IMPLEMENTED_NOT_EXECUTED` |
| `backend/app/security/` | `injection.py`, `redaction.py` | `IMPLEMENTED_NOT_EXECUTED` |
| `backend/app/audit/` | `chain.py` | `IMPLEMENTED_NOT_EXECUTED` - **never called from the API** |
| `backend/app/services/` | `auth_service.py`, `assessment_service.py` | `IMPLEMENTED_NOT_EXECUTED` |
| `backend/app/api/` | `app.py` (Flask, 10 routes) | `PARTIAL` - **authorization decorator applied to no route** |
| `backend/app/policy/`, `actions/` | `policy_gateway.py`, `action_gateway.py` | `PARTIAL` - not wired to the API |
| `backend/app/verification/` | `evidence_verifier.py` | `IMPLEMENTED_NOT_EXECUTED` |
| `backend/app/database/` | `seed_corpus.py` | `IMPLEMENTED_NOT_EXECUTED` - **no schema DDL exists** |
| `scripts/` | `run_assessment.py`, `offline_self_test.py`, `seed_demo.py`, `_bootstrap.py` | `IMPLEMENTED_NOT_EXECUTED` |

## Empty packages - NOT implementation

`agents/` · `llm/` · `graph/` · `orchestration/` · `reports/` · `repositories/` · `tools/` · `ports/` · `prompts/` · `connectors/` · `config/` · `database/migrations/` · `api/routers/`

Each contains only an empty `__init__.py`. **No frontend directory exists anywhere in the repository.**

## Tests that exist (8 files - none executed in-session, no CI)

`tests/unit/test_audit_chain.py` · `tests/unit/rules/test_confidence.py` · `tests/unit/rules/test_readiness.py` · `tests/integration/test_api_endpoints.py` · `tests/integration/test_corpus_pipeline.py` · `tests/security/test_ingestion_boundary.py` · `tests/security/test_injection_scanner.py` · `tests/smoke/test_offline_readiness.py`

## Research corpus

17 real sources across 8 topic folders. See [`research/RESEARCH_INDEX.md`](research/RESEARCH_INDEX.md). `research/Surveys/` is empty of papers.

## Launchers

`START_GXP_SENTINEL.bat` (runs an assessment, not an application) · `RUN_OFFLINE_SELF_TEST.bat` · `start_gxp_sentinel.sh` · `run_offline_self_test.sh`. **`RUN_ASSESSMENT.bat` is missing.** None has been executed or verified on Windows.
