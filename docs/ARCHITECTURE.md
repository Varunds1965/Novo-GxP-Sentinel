# Architecture

**PROTOTYPE - SYNTHETIC DATA - NOT VALIDATED FOR PRODUCTION GxP USE**
*Not a compliance certification.*

## Layered Architecture

```
┌──────────────────────────────────────────────────────┐
│ Frontend Layer (M9)                                   │
│ Nine workspaces: Command Centre, Copilot, Audit      │
│ Readiness, Graph, Changes, Access, Approvals, Lab    │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│ API Layer (M3)                                       │
│ Flask routes, StandardResponse envelope, trace_id    │
│ Authentication (token-based)                         │
│ Authorization (require_permission decorator)         │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│ Orchestration Layer (M6)                             │
│ Agent supervisor, turn/call/runtime limits           │
│ Policy gateway, action gateway, approval requirements│
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│ Service Layer                                        │
│ Assessment, Authentication, RAG, Graph, Approval     │
│ Copilot (M5), Agents (M6), Assurance Lab (M8)       │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│ Domain Layer (M0)                                    │
│ Frozen dataclasses (User, SourceRecord, Finding)    │
│ Enumerations (Role, Severity, Status)                │
│ Immutable, zero I/O, testable in isolation          │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│ Rules & Logic Layer (M2)                             │
│ Checklist engine, confidence, readiness, applicability│
│ Deterministic scoring, no LLM dependency            │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│ Evidence Layer (M1, M5)                              │
│ Ingestion, extraction, chunking, injection scanning  │
│ Quarantine, hashing, metadata, retrieval (FTS5)      │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│ Storage Layer                                        │
│ SQLite database with schema for all entities         │
│ Graph nodes/edges, evidence, findings, approvals     │
└──────────────────────────────────────────────────────┘
```

## Data Model

### Core Entities

**User**
- id: str (UUID)
- username: str (unique)
- password_hash: str (bcrypt/SHA-256)
- role_id: str → Role.id
- created_at: datetime

**Role**
- id: str (enum: SYSTEM_OWNER, QA_REVIEWER, AUDITOR, LEADERSHIP_VIEWER, SECURITY_TESTER)
- name: str
- description: str

**SourceRecord** (ingested evidence)
- source_id: str (unique)
- title: str
- document_type: str
- system_id: str
- version: str
- approval_status: enum
- trust_level: enum (TRUSTED, UNTRUSTED_REVIEW_REQUIRED, QUARANTINED_UNTRUSTED)
- content_hash: str (SHA-256)
- source_system: str (where it came from)
- ingested_at: datetime
- effective_date: datetime (when it becomes applicable)
- review_date: datetime (when it was last reviewed)
- owner: str
- byte_size: int
- page_count: int
- injection_findings: list[str] (findings from security scan)

**EvidenceRef** (pointer to excerpt)
- source_id: str → SourceRecord.source_id
- title: str
- location: str (page, section, line range)
- content_hash: str
- version: str
- relevant_excerpt: str (<600 chars, verbatim)
- retrieved_at: datetime
- effective_date: datetime
- review_date: datetime

**Assessment**
- id: str (UUID)
- system_id: str
- user_id: str → User.id
- status: enum (PENDING, RUNNING, COMPLETE)
- created_at: datetime
- completed_at: datetime
- mode: enum (DETERMINISTIC_FALLBACK, LOCAL_AI)

**Finding**
- id: str (UUID)
- assessment_id: str → Assessment.id
- control_id: str
- category: enum
- severity: enum (INFO, LOW, MEDIUM, HIGH, CRITICAL)
- confidence: enum (HIGH, MEDIUM, LOW, INSUFFICIENT_EVIDENCE)
- evidence_refs: list[EvidenceRef]
- status: enum (OPEN, CONFLICT, INSUFFICIENT_EVIDENCE, HUMAN_REVIEW_REQUIRED, CLOSED)
- created_at: datetime

**ApprovalDecision**
- id: str (UUID)
- proposal_id: str
- decided_by: str → User.id
- decision: enum (APPROVED, REJECTED, CLARIFICATION_REQUESTED)
- decision_note: str (>= 10 chars)
- decided_at: datetime

**AuditLogEntry**
- id: str (UUID)
- user_id: str → User.id (nullable for system actions)
- action: str (LOGIN, LOGOUT, START_ASSESSMENT, RUN_ASSESSMENT, INGEST_EVIDENCE, etc.)
- resource_type: str (AUTH, ASSESSMENT, EVIDENCE, APPROVAL, etc.)
- resource_id: str
- details: str
- result: enum (SUCCESS, FAILED, DENIED)
- timestamp: datetime
- trace_id: str (correlation ID)

**Change**
- id: str (UUID)
- system_id: str
- change_type: str
- description: str
- created_by: str → User.id
- created_at: datetime
- implemented_at: datetime
- status: enum (PROPOSED, APPROVED, IMPLEMENTED, ROLLED_BACK)

**Incident**
- id: str (UUID)
- system_id: str
- title: str
- description: str
- severity: enum
- reported_by: str → User.id
- reported_at: datetime
- resolved_at: datetime
- status: enum (OPEN, INVESTIGATING, RESOLVED, CLOSED)

**GraphNode**
- id: str (UUID)
- node_type: enum (SYSTEM, REQUIREMENT, CONTROL, RISK, TEST, EVIDENCE, DOCUMENT, FINDING, CHANGE, INCIDENT, APPROVAL)
- label: str
- attributes: dict[str, str]

**GraphEdge**
- id: str (UUID)
- source_id: str → GraphNode.id
- target_id: str → GraphNode.id
- edge_type: enum (REQUIRES, SATISFIED_BY, VERIFIED_BY, CHANGED_BY, IMPACTS, OWNED_BY, REVIEWED_BY, REFERENCES, EVIDENCES, RAISES, RECOMMENDS, APPROVED_BY)
- attributes: dict[str, str]

### Relationships

```
System
  ├─ REQUIRED_BY → Requirement
  │   ├─ SATISFIED_BY → Control
  │   │   ├─ VERIFIED_BY → Test
  │   │   │   └─ EVIDENCED_BY → Evidence
  │   │   │       └─ PROVES → Finding
  │   │   └─ IMPACTS ← Change
  │   └─ RAISES ← Incident
  │
  ├─ Changes
  │   └─ APPROVED_BY → Approval
  │
  ├─ Incidents
  │   └─ RESOLVED_BY → Change
  │
  └─ AccessAssignments
      └─ GRANTED_TO → User
          └─ HAS_ROLE → Role
```

## Deterministic vs. AI Modes

### DETERMINISTIC_FALLBACK (M0-M2)

Works without any model:

1. **Ingestion** - Parse documents, extract metadata, detect injection
2. **Chunking** - Split by section, create excerpts
3. **Indexing** - FTS5 full-text search
4. **Retrieval** - Keyword matching, ranking by TF-IDF
5. **Checklist** - 350 auditor questions → deterministic evaluation
6. **Confidence** - Based on evidence coverage, document status, review dates
7. **Findings** - Deterministic rule outcomes
8. **Readiness** - Calculated from findings, not model-generated

**Guarantee:** 100% grounded in real evidence, no hallucination risk.

### LOCAL_AI (M5, optional)

Optionally enhances with local model:

1. Same retrieval as DETERMINISTIC_FALLBACK
2. Model answer generation (if model available)
3. Side-by-side comparison of deterministic vs. model
4. User chooses which to trust
5. Falls back to deterministic if model unavailable

**Design:** Model output is *advice*, not *finding*. Findings always come from deterministic logic.

**No mandatory cloud API.** Local llama.cpp models are optional; deterministic mode always works.

## API Response Envelope

Every response (success or error):

```json
{
  "success": true|false,
  "data": { ... } or null,
  "error": "message" or null,
  "trace_id": "uuid",
  "timestamp": "2026-08-28T10:30:00Z"
}
```

**Trace ID:** Unique per request, logged in audit trail, returned to client. Allows request tracing end-to-end.

**Timestamp:** Server time when response was generated. Client can detect skew.

## Security Architecture

### Authentication

Token-based (JWT-like, not cryptographic in prototype):

1. User sends `username` + `password`
2. Server hashes password, compares to stored hash
3. Server generates token, stores token → user_id mapping with expiry
4. Client sends token in `Authorization: Bearer` header
5. Server verifies token is fresh, returns User object
6. Subsequent requests use user identity from verified token

### Authorization

Role-based access control (RBAC):

1. User has a Role (SYSTEM_OWNER, QA_REVIEWER, etc.)
2. Role has Permissions (READ, INGEST, PROPOSE, APPROVE, RUN_ASSURANCE_LAB)
3. Each permission is scoped to a Resource (ASSESSMENT, EVIDENCE, GRAPH, APPROVALS)
4. API route checks: `require_permission(user, action, resource)`
5. If no permission, returns 403 Forbidden
6. All permission checks are logged to audit trail

### Audit Trail

Every material action is logged:

```
user_id | action | resource_type | resource_id | result | timestamp | trace_id
```

Enables:
- Who did what when
- Approval audit
- Change tracking
- Compliance reporting
- Forensics

### Evidence Integrity

1. **Content Hash** - SHA-256 of source document
2. **Chunk Hash** - SHA-256 of each excerpt
3. **Provenance** - source_id, location, version, review_date
4. **Trust Level** - TRUSTED, UNTRUSTED_REVIEW_REQUIRED, QUARANTINED_UNTRUSTED
5. **Injection Scan** - Each source scanned for prompt injection attempts
6. **Quarantine** - Suspicious documents marked QUARANTINED_UNTRUSTED
7. **Currency** - Evidence expires if review_date passes

Findings reference EvidenceRef objects, which include:
- Verbatim excerpt (not model-generated summary)
- Exact location (page, section, line)
- Document version (so re-review detects stale evidence)
- Review date (so expiration is detected)

## Module Organization

```
backend/app/
├── api/              Routes, Flask app, schemas
├── services/         Business logic (Auth, Assessment, RAG, Copilot, etc.)
├── domain/           Immutable models, enums, errors
├── rules/            Checklist engine, confidence, readiness, applicability
├── rag/              Ingestion, chunking, extraction, retrieval
├── security/         Injection detection, redaction
├── audit/            Audit chain logging
├── database/         SQLite schema, connection, migrations
├── agents/           (M6 stub) Agent implementations
├── graph/            (M7 stub) Graph construction and queries
├── orchestration/    (M6 stub) Agent orchestration with safety limits
├── llm/              (M5 stub) Local LLM adapter
├── policy/           Policy gateway (allowed/denied decisions)
├── actions/          Action gateway (dry-run, preconditions)
├── verification/     Evidence verification
├── reports/          (M10 stub) Report generation
├── repositories/     (stub) Data repositories (unused)
├── tools/            (M6 stub) Agent tools
├── prompts/          (stub) Prompt templates
├── ports/            (stub) External ports/adapters
└── config/           (stub) Configuration
```

## Determinism Guarantee

The project asserts:

**DETERMINISTIC_FALLBACK and LOCAL_AI modes must produce identical authoritative findings.**

Where they differ:
- Same finding IDs, severity, confidence
- Same evidence references
- Same readiness score
- Only narrative explanation may differ

**Test:** `tests/` should include mode-parity tests comparing outputs side-by-side.

## No Unilateral AI Authority

Core principle:

> AI output is *advice*, never *decision*.

Designs enforcing this:

1. **Approval gateway** - GxP-relevant writes require human approval
2. **Policy gateway** - Evaluates whether action is allowed; returns reason code, not binary yes/no
3. **Audit trail** - All actions logged; enables post-hoc review
4. **Evidence grounding** - All findings cite specific evidence locations
5. **Confidence/uncertainty** - Findings report confidence and limitations explicitly
6. **Abstention** - System refuses to answer unsupported questions
7. **Orchestration limits** - Agent loops have maximum turns, calls, runtime

## Off-Line Guarantee

Core functionality works without internet:

1. No cloud API calls (OpenAI, Anthropic, etc.)
2. No external model downloads at runtime
3. No outbound network calls from core logic
4. Deterministic fallback is always available
5. Evidence is stored locally (SQLite)

## Version 1.0 Scope

M0-M10 as defined in the Constitution covers:

- Evidence-based readiness assessment
- Deterministic + optional local AI
- Role-based access control
- Approval workflow foundation
- Evidence graph foundation
- Agent framework foundation
- Assurance Lab security scenarios
- Nine workspaces (designs, not all built)

Production path would require:
- Validation against real systems
- Formal security review
- Compliance certification
- Deployment hardening
- Disaster recovery
- High availability setup
