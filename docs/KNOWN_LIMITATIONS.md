# Known Limitations

**PROTOTYPE - SYNTHETIC DATA - NOT VALIDATED FOR PRODUCTION GxP USE**
*Not a compliance certification.*

## Environmental Limitations

This session was executed against the GitHub repository via API. The following **cannot be claimed as verified** without Windows execution:

- Database initialization
- Server startup
- Test execution
- API functionality
- Authentication/authorization (code-level only)
- Evidence upload
- Assessment execution
- Report generation
- Frontend rendering

See `docs/WINDOWS_VERIFICATION.md` for step-by-step verification instructions.

## Feature Limitations

### M4: Auditor Challenges

- **Missing:** 25 scenarios not extracted from mentor material
- **Impact:** Cannot run full assessment; findings incomplete
- **Mitigation:** Specifications exist in `docs/AI_PROJECT_CONSTITUTION.md` and `docs/GxP_Sentinel_Visual_User_Manual.pdf`; manual extraction required

### M5: Copilot

- **Missing:** No evidence-grounded question-answering service
- **Missing:** No abstention logic (system does not know when to say "I don't know")
- **Impact:** Cannot use Copilot; RAG retrieval works but is not exposed as a service
- **Mitigation:** Deterministic fallback works for assessment; Copilot would add optional AI enhancement

### M5: Local LLM

- **Missing:** No llama.cpp or other local model integration
- **Missing:** Model not downloaded, installed, or tested
- **Status:** Fallback to DETERMINISTIC_FALLBACK is the working baseline
- **Impact:** LOCAL_AI mode is unavailable; deterministic mode is always used
- **Mitigation:** Mode parity is not required to demonstrate (only one mode works); can be added later as enhancement

### M6: Agents

- **Missing:** 7 agents (A0-A7) not implemented
- **Missing:** Orchestration framework not built
- **Impact:** No autonomous agent capability; assessment is purely deterministic
- **Mitigation:** Deterministic engine is fully functional standalone

### M7: Evidence Graph

- **Missing:** Graph construction not implemented
- **Missing:** Cross-record reconciliation detectors not implemented
- **Missing:** Graph visualization UI not built
- **Impact:** Cannot visualize evidence relationships; all queries are linear
- **Mitigation:** All evidence is traceable via text search and audit trail

### M8: Approval Workflow

- **Missing:** Approval service not implemented
- **Missing:** Approval UI not built
- **Missing:** Assurance Lab scenarios (S1-S7) not implemented
- **Impact:** No human-in-the-loop approval; all proposed actions are blocked (501 error)
- **Mitigation:** Deterministic assessment and findings are complete; approvals would add optional workflow

### M9: Frontend

- **Missing:** All 9 workspaces not built
- **Missing:** No HTML/CSS/JavaScript
- **Missing:** No static file serving
- **Impact:** No user interface; API is JSON-only
- **Mitigation:** API is fully functional via `curl` or REST clients; frontend is optional UI layer

## Security Limitations

### No TLS

Prototype runs on HTTP only. Production would require:
- TLS 1.2+ (HTTPS)
- Certificate management
- Secure key storage

### No Rate Limiting

No per-user or per-endpoint request throttling. Prototype is designed for low-volume testing.

### Prototype Password Hashing

Authentication uses SHA-256 for prototype simplicity. Production would require:
- bcrypt or argon2
- Salting
- Work factors
- Password policies

### No CSRF Protection

No cross-site request forgery tokens. Forms are not protected.

### Shared SQLite Connection

Development server may fail under concurrent requests due to SQLite's write-lock model. Production would require:
- Connection pooling
- Thread-safe connection management
- PostgreSQL or other multi-writer database

## Data Limitations

### All Assessment Data is Synthetic

- No real company evidence
- No real system records
- No real compliance findings
- All demonstration data is labeled `SYNTHETIC_DEMONSTRATION_DATA - NOT_COMPANY_EVIDENCE`

### Baseline is Correct but Static

- M0-M2 baseline: readiness 29/100, 169 findings, 0 critical
- This is the **only** known truthful result
- All other assessment results must be verified against real evidence before use

### No Production Data Ingestion

The system is designed to ingest company evidence but has not been connected to:
- Document repositories
- Test result systems
- Change management systems
- Incident tracking systems
- Audit repositories

## Compliance Limitations

### NOT a Compliance Certification

- This software has not been validated against any regulatory standard
- Findings are not compliance findings
- Readiness score is not a compliance assessment
- Approvals are not electronic signatures under 21 CFR Part 11

### NOT Suitable for Production GxP Use

- Prototype quality code
- No formal testing
- No validation plan
- No configuration management
- No change control process
- No disaster recovery
- No business continuity

### Research Corpus is Informational Only

Included research papers (GraphRAG, RAG, agents, explainability, NIST AI Risk Management, OWASP GenAI Top 10) are:
- Background material for design decisions
- Not validation evidence
- Not regulatory guidance
- Informative references only

## Performance Limitations

### No Benchmarks

No performance metrics were measured in this session because execution is blocked. Unknown:
- Startup time
- API response time
- Database query time
- Assessment runtime
- Memory footprint
- Concurrent user capacity

### SQLite Constraints

- Single-file embedded database
- Not suitable for high concurrency
- Not suitable for large datasets (>10GB)
- Not suitable for distributed deployment

## Operational Limitations

### No Monitoring

No built-in monitoring, alerting, or observability beyond:
- Audit log (manually queryable)
- API health endpoint
- HTTP status codes

### No Logging Configuration

Logging is hardcoded in each module. Production would need:
- Centralized logging
- Log levels (DEBUG, INFO, WARN, ERROR)
- Log rotation
- Log aggregation

### No Error Recovery

- No retry logic
- No circuit breakers
- No graceful degradation
- No fallback mechanisms (except deterministic baseline for LOCAL_AI)

## Documentation Limitations

### Mentor Material Not Extracted

Two key documents exist but have not been fully processed:
- `docs/AI_PROJECT_CONSTITUTION.md` (binding specification, 157 KB) - Not fully extracted into code
- `docs/GxP_Sentinel_Visual_User_Manual.pdf` (UI specification, 2.4 MB) - Not built into frontend

### Research Citations Not Reconciled

The 17 source papers in `research/` are present but not fully traced to every design decision and code location.

## Known Outstanding Issues

1. **Authorization incomplete** - Decorator not applied to all protected routes (M3)
2. **Evidence upload missing** - API endpoint is 501; ingestion pipeline exists but unreachable
3. **M4 not extracted** - 25 auditor challenges remain in mentor material as templates
4. **Copilot service missing** - RAG retrieval works; wrapper service does not
5. **No approval workflow** - Gateway exists; service and UI do not
6. **No Assurance Lab** - 7 scenarios designed but not implemented
7. **No frontend** - All 9 workspaces are unbuilt
8. **No CI/CD** - No automated testing or deployment pipeline

## Workarounds & Mitigations

### For Missing Frontend
- Use `curl` to call API endpoints
- Use Postman or REST client
- Call endpoints from scripts

### For Missing Copilot
- Use RAG retrieval directly via API (if endpoint is built)
- Use deterministic checklist engine for assessment

### For Missing Approval Workflow
- All write actions are currently blocked
- Will be unblocked after approval service is implemented

### For Missing Agents
- Assessment is fully functional with deterministic rules
- Agents would add optional automation; not required for assessment

### For Missing Local LLM
- DETERMINISTIC_FALLBACK mode is always available
- All findings and readiness scores use deterministic logic
- No cloud API dependency

## Future Work

To remove these limitations:
1. Windows verification (unblocks all execution claims)
2. M4 challenge extraction (unblocks full assessment)
3. M5 Copilot implementation (unblocks Copilot workspace)
4. M6 agent implementation (unblocks agent automation)
5. M7 graph implementation (unblocks evidence graph workspace)
6. M8 approval + Assurance Lab (unblocks human control + testing)
7. M9 frontend build (unblocks user interface)
8. CI/CD setup (unblocks continuous integration)
9. Security hardening (unblocks production path)
10. Local LLM integration (unblocks optional AI enhancement)
