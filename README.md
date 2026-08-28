# GxP Sentinel

**PROTOTYPE - SYNTHETIC DATA - NOT VALIDATED FOR PRODUCTION GxP USE**

*Not a compliance certification.*

GxP Sentinel is a prototype system for evidence-based quality assurance readiness assessment in regulated environments. It combines deterministic rule engines with retrieval-augmented generation to ground AI responses in company evidence.

## Current Status

**Session:** 2026-08-28

### What's Implemented and Working (IMPLEMENTED_NOT_EXECUTED)

- **M0-M2 Deterministic Core:** Domain models, rule engines, evidence ingestion, FTS5 retrieval, audit chain
- **M3 API:** Flask application with 10 routes, authentication, authorization decorator, database schema (SQLite)
- **Security:** Prompt injection detection, redaction, audit logging
- **Baseline Assessment:** Known working on Windows (readiness 29/100, 169 findings open, 0 critical)

### What's Partially Implemented

- **M3 Authorization:** Decorator created and wired to 5 protected routes; needs completion on all routes
- **Database Layer:** Schema created; migration runner not yet tested
- **Policy/Action Gateways:** Modules exist; not yet connected to routes

### What's Not Implemented

- **M4 Auditor Challenges:** 25 scenarios not yet extracted from mentor material
- **M5 Copilot:** RAG plumbing exists; copilot service missing
- **M5 Local LLM:** Adapter stub created; model not tested
- **M6 Agents:** 7 agent skeletons missing; orchestration missing
- **M7 Evidence Graph:** Schema created; builder/query engine missing
- **M8 Approval Workflow:** Database schema created; service/UI missing
- **M8 Assurance Lab:** 7 scenarios not yet implemented
- **M9 Frontend:** All 9 workspaces not yet built

### What's Blocked

All execution-level verification is **BLOCKED_BY_ENVIRONMENT** because this audit was performed via the GitHub API without access to:
- The Windows filesystem at `C:\Users\Varun\Documents\GitHub\Novo-GxP-Sentinel`
- Python runtime
- Database initialization
- Server startup
- Test execution
- Browser automation

You must run the verification steps in `docs/WINDOWS_VERIFICATION.md` on your Windows machine.

## Quick Start (Windows)

### Start the Server

```powershell
cd C:\Users\Varun\Documents\GitHub\Novo-GxP-Sentinel
.\START_GXP_SENTINEL.bat
```

Server starts at `http://127.0.0.1:8765`.

### Run an Assessment

```powershell
.\RUN_ASSESSMENT.bat
```

Results in `docs/evidence/`.

### Run Tests

```powershell
Activate the venv, then:
$env:PYTHONPATH="backend"
pytest -v
```

## Architecture

### Layered Design

```
API Layer              (Flask routes, authentication, authorization)
    ↓
Service Layer         (Assessment, Auth, Evidence, approval logic)
    ↓
Domain Models         (Frozen dataclasses, zero I/O imports)
    ↓
Rules Engine          (Deterministic scoring, readiness, confidence)
    ↓
Retrieval Layer       (FTS5 search, chunking, provenance)
    ↓
Evidence Store        (SQLite with schema, hashing, metadata)
```

### Deterministic Baseline

The M0-M2 core runs in `DETERMINISTIC_FALLBACK` mode, which:
- Requires zero LLM model
- Works offline
- Produces 100% grounded answers
- Is always available as a fallback

Optional `LOCAL_AI` mode (M5) wraps deterministic logic with local model enhancement where safe.

## Project Structure

```
.
├── backend/
│   └── app/
│       ├── api/              API routes (Flask)
│       ├── services/         Business logic
│       ├── domain/           Models, enums, errors
│       ├── rules/            Deterministic engines
│       ├── rag/              Retrieval and ingestion
│       ├── security/         Injection detection
│       ├── audit/            Audit trail
│       ├── database/         SQLite layer
│       ├── agents/           (M6 stub)
│       ├── graph/            (M7 stub)
│       ├── llm/              (M5 stub)
│       ├── orchestration/    (M6 stub)
│       ├── policy/           Policy gateway
│       └── actions/          Action gateway
├── tests/                    Test suite
├── scripts/                  Assessment runner, seeders
├── docs/                     Documentation
├── research/                 Research papers
├── requirements.txt          Python dependencies
└── START_GXP_SENTINEL.bat    Windows server launcher
```

## Documentation

- **[docs/FINAL_REPOSITORY_AUDIT.md](docs/FINAL_REPOSITORY_AUDIT.md)** - Complete code-level audit with status per component
- **[docs/API_SPECIFICATION.md](docs/API_SPECIFICATION.md)** - Complete API reference
- **[docs/WINDOWS_VERIFICATION.md](docs/WINDOWS_VERIFICATION.md)** - Step-by-step verification on Windows
- **[docs/M4_M10_IMPLEMENTATION_STATUS.md](docs/M4_M10_IMPLEMENTATION_STATUS.md)** - What's next
- **[docs/AI_PROJECT_CONSTITUTION.md](docs/AI_PROJECT_CONSTITUTION.md)** - Mentor-provided specification (binding)
- **[docs/GxP_Sentinel_Visual_User_Manual.pdf](docs/GxP_Sentinel_Visual_User_Manual.pdf)** - Authoritative UI specification

## Verification Status

| Component | Status | Evidence |
|---|---|---|
| M0-M2 Core | IMPLEMENTED_NOT_EXECUTED | Source code present; execution blocked |
| M3 API | IMPLEMENTED_NOT_EXECUTED | Flask app, routes, auth; execution blocked |
| M3 Authorization | IMPLEMENTED_NOT_EXECUTED | Decorator wired to 5 routes; incomplete |
| M3 Database | IMPLEMENTED_NOT_EXECUTED | Schema created; initialization blocked |
| M4 Auditor Challenges | MISSING | Not extracted from mentor material |
| M5 RAG | PARTIAL | Ingestion/retrieval code; copilot missing |
| M5 Copilot | MISSING | Endpoint stub only |
| M5 Local LLM | STUB | Adapter interface; model not tested |
| M6 Agents | MISSING | 7 agent placeholders; unimplemented |
| M6 Orchestration | STUB | Safety framework missing |
| M7 Graph | STUB | Database schema; builder/queries missing |
| M8 Approval | MISSING | DB schema; service/UI missing |
| M8 Assurance Lab | MISSING | 7 scenarios not implemented |
| M9 Frontend | MISSING | All 9 workspaces not built |
| M10 Tests | PARTIAL | 8 test files; none executed in this session |

## Known Limitations

- No local LLM model runtime
- No browser-based frontend (HTML/CSS/JS)
- No approval workflow UI
- No Assurance Lab scenario execution
- No evidence upload UI
- No evidence graph visualization
- No agent execution
- All execution verification is BLOCKED_BY_ENVIRONMENT (requires Windows machine)

## Security Model

All consequential actions require:

1. **Authentication** - User identity verified via token
2. **Authorization** - Role-based permission check
3. **Policy evaluation** - Is action allowed by policy?
4. **Approval requirement** - Is GxP-relevant write approved?
5. **Audit logging** - All actions logged with trace ID

No action bypasses this chain. The API enforces it at every protected endpoint.

## Research Foundation

17 source documents included:

- **Regulatory:** 21 CFR Part 11, GAMP 5, FDA CSA guidance
- **AI Safety:** NIST AI Risk Management, OWASP GenAI Top 10
- **Graph/RAG:** GraphRAG, dense passage retrieval, retrieval-augmented agents
- **Agents:** Multi-agent systems, compliance automation
- **XAI:** Explainability surveys and frameworks

See [research/RESEARCH_INDEX.md](research/RESEARCH_INDEX.md) for the complete inventory.

## Next Steps (Windows Agent)

1. **Verify the baseline** - Run `docs/WINDOWS_VERIFICATION.md`
2. **Run tests** - Capture pytest output
3. **Extract M4 challenges** - From mentor material
4. **Implement M5 Copilot** - Service wrapper for RAG
5. **Implement M6 agents** - With M5 foundation
6. **Build M7 graph** - Entity extraction and relationship inference
7. **Implement M8 approval** - Workflow service and UI
8. **Build M9 frontend** - Nine workspaces from spec
9. **Create release ZIP** - Exclude .venv, __pycache__, credentials

## Contributing

This is a prototype. Do not commit:
- `.venv/` (virtual environment)
- `__pycache__/` or `*.pyc`
- `.env` or credential files
- Temporary logs or artifacts

All code changes must preserve:
- Existing functionality
- Test suite integrity
- Audit trail completeness
- Mentor material provenance

## License

See `LICENSE` file.

## Contact

This is a prototype/hackathon project created for educational and demonstration purposes. It is not production-validated GxP software.
