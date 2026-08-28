# Project Knowledge Index (Updated)

**PROTOTYPE - SYNTHETIC DATA - NOT VALIDATED FOR PRODUCTION GxP USE**
*Not a compliance certification.*

This index reflects the **actual state of the repository** as of 2026-08-28 10:56 AM.

## Key Documents

### Status & Audit (READ THESE FIRST)

- [**docs/FINAL_REPOSITORY_AUDIT.md**](docs/FINAL_REPOSITORY_AUDIT.md) - Comprehensive code audit with exact status per component
- [**docs/FINAL_PROJECT_STATUS.md**](docs/FINAL_PROJECT_STATUS.md) - Matrix of all 19 components with evidence
- [**docs/WINDOWS_VERIFICATION.md**](docs/WINDOWS_VERIFICATION.md) - Step-by-step verification instructions for Windows
- [**docs/KNOWN_LIMITATIONS.md**](docs/KNOWN_LIMITATIONS.md) - Honest list of what doesn't work

### Specifications (BINDING)

- [**docs/AI_PROJECT_CONSTITUTION.md**](docs/AI_PROJECT_CONSTITUTION.md) - Mentor-provided (157 KB, binding)
- [**docs/Codex Prototype prompt.txt**](docs/Codex%20Prototype%20prompt.txt) - Mentor-provided (76 KB)
- **docs/GxP_Sentinel_Visual_User_Manual.pdf** - Mentor-provided UI spec (2.4 MB)

### Implementation Guides (READ BEFORE CODING)

- [**docs/API_SPECIFICATION.md**](docs/API_SPECIFICATION.md) - Complete API reference with all endpoints
- [**docs/ARCHITECTURE.md**](docs/ARCHITECTURE.md) - Layered design, data model, relationships
- [**docs/M4_M10_IMPLEMENTATION_STATUS.md**](docs/M4_M10_IMPLEMENTATION_STATUS.md) - What's next, in priority order

### What's Actually in the Repository

| Area | Status | Location |
|---|---|---|
| M0-M2 Core | IMPLEMENTED_NOT_EXECUTED | `backend/app/domain/`, `rules/`, `rag/`, `security/`, `audit/` |
| M3 API | IMPLEMENTED_NOT_EXECUTED | `backend/app/api/app.py` (10 routes) |
| M3 Database | IMPLEMENTED_NOT_EXECUTED | `backend/app/database/__init__.py` (complete DDL) |
| M3 Auth | IMPLEMENTED_NOT_EXECUTED | `backend/app/services/auth_service.py` |
| M3 Authorization | PARTIAL | Decorator wired to 5 routes; others exposed |
| M4-M10 Stubs | DOCUMENTED | Each module has placeholder with BLOCKED marker |
| Windows Launchers | CREATED | `START_GXP_SENTINEL.bat`, `RUN_ASSESSMENT.bat` |
| Tests | EXIST_NOT_EXECUTED | 8 files in `tests/`; none have been run |
| Frontend | MISSING | No HTML/CSS/JS anywhere |
| Research | REAL | 17 papers in `research/`; indexes empty |
| Docs | COMPLETE | Status, API, architecture, limitations all written |

## Verification Status

**Nothing is VERIFIED without execution evidence.**

All claims in this index are either:
- `IMPLEMENTED_NOT_EXECUTED` - Source code exists; behavior not observed
- `MISSING` - Feature does not exist
- `PARTIAL` - Partially complete; see details
- `STUB` - Placeholder with no implementation
- `DOCUMENTED_ONLY` - Specification exists; code does not

**Execution verification is BLOCKED_BY_ENVIRONMENT:** Requires Windows machine, Python, pytest, Flask, database initialization, server startup.

## How to Use This Index

### If you're developing...

1. Read the specification: Constitution, Visual Manual, API spec
2. Check the audit: FINAL_REPOSITORY_AUDIT.md
3. Check the status: FINAL_PROJECT_STATUS.md
4. Follow the priority: M4_M10_IMPLEMENTATION_STATUS.md section R

### If you're verifying...

1. Follow WINDOWS_VERIFICATION.md
2. Capture test output
3. Check readiness is still 29/100 (not artificially improved)
4. Record actual pass/fail counts
5. Update TEST_EXECUTION_REPORT.md with real numbers

### If you're deploying...

1. This is a **prototype**, not production software
2. Read KNOWN_LIMITATIONS.md
3. Expect to perform security audit, compliance validation, load testing
4. Do not claim regulatory validation
5. Do not use synthetic data in production

## What Actually Works (Baseline)

**From a real Windows run (not this session):**

- System: NL-MES-001
- Readiness: 29/100
- Findings: 169 (0 critical)
- Grounded answer rate: 175/175 = 100%
- Mode: DETERMINISTIC_FALLBACK

This baseline is **golden**. Do not artificially improve it. If it changes, document why.

## What Definitely Doesn't Work

- **M4 challenges:** Not implemented (must extract manually)
- **M5 Copilot:** Endpoint returns 501
- **M6 Agents:** Missing (7 placeholders)
- **M7 Graph:** Missing (schema only)
- **M8 Approval:** Missing (gateway exists, workflow does not)
- **M8 Assurance Lab:** Missing (7 scenarios not implemented)
- **M9 Frontend:** Missing (all 9 workspaces not built)
- **CI/CD:** Missing (no GitHub Actions)
- **Local LLM:** Unavailable (fallback is deterministic)

## Key Decisions

### Fixed Defects (This Session)

1. **User import failure** → Added User dataclass to models.py
2. **Authorization not wired** → Applied @require_permission to 5 routes
3. **Missing database schema** → Created complete DDL with initialization

### Preserved Decisions

1. **Deterministic baseline** - M0-M2 assessment is purely rule-based, no model needed
2. **Offline-first** - No mandatory cloud API
3. **Evidence grounding** - All findings cite source locations
4. **Human in the loop** - GxP-relevant writes require approval
5. **Audit trail** - All actions logged with trace ID

## Research Materials (Real)

17 source documents in `research/`:

- **Regulatory:** 21 CFR Part 11, GAMP 5, FDA CSA guidance
- **AI Safety:** NIST AI Risk Management, OWASP GenAI Top 10
- **Graph/RAG:** GraphRAG paper, dense passage retrieval, retrieval-augmented agents
- **Agents:** Multi-agent systems, compliance automation
- **XAI:** Explainability surveys and frameworks

See research/RESEARCH_INDEX.md for exact inventory. All papers are real; no citations are fabricated.

## Next Session Priorities

1. **Windows verification** (unblocks all execution claims)
2. **M4 challenge extraction** (unblocks full assessment)
3. **M5 Copilot implementation** (unblocks Copilot workspace)
4. **M8 approval workflow** (unblocks approval workspace)
5. **M9 frontend build** (unblocks all UI workspaces)

## How This Index Changes

This file should be updated whenever:
- A major feature is completed
- An execution test is run and results are captured
- A known limitation is resolved
- A blocker is unblocked
- Documentation is added

**Do NOT change status claims without execution evidence.**
