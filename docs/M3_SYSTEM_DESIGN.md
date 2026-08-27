# M3: System Design - Backend Integration Layer

**Status**: M3 IMPLEMENTATION IN PROGRESS  
**Date**: 27 August 2026  
**Milestone**: Backend services integration, API framework, authorization layer

---

## M3 OBJECTIVES

**Primary Goal**: Integrate the M0-M2 deterministic core with an HTTP API and service layer, making the assessment engine callable from external clients.

**Scope**:
- HTTP API framework (Flask-based)
- Authentication and authorization (user/role management)
- Service layer (business logic coordination)
- Evidence verification (claim grounding)
- Policy gateway (permission enforcement)
- Action gateway (mock execution, dry-run, audit logging)
- Database finalization (users, roles, permissions, assessments, approvals)
- Integration tests

**NOT in scope for M3**:
- UI/Frontend (M9)
- Local AI runtime integration (M5)
- Agent orchestration (M6)
- Evidence graph (M7)
- Export workflows (M8)

---

## ARCHITECTURE OVERVIEW

### M3 Layers

```
CLIENT (HTTP requests)
    ↓
API LAYER (Flask routes, request validation, response formatting)
    ↓
SERVICE LAYER (business logic, orchestration, transactions)
    ↓
DOMAIN LAYER (models, enums, validation)
    ↓
DETERMINISTIC CORE (M0-M2: rules engine, ingestion, audit)
    ↓
PERSISTENCE LAYER (SQLite database)
```

### Request Flow

```
1. Client POST /api/v1/assessment/start
        ↓
2. Flask validates request, extracts token from Authorization header
        ↓
3. AuthService verifies token (check if valid, not expired)
        ↓
4. Policy Gateway checks if user's role can create assessments
        ↓
5. AssessmentService.start_assessment() creates record in database
        ↓
6. Return StandardResponse with assessment ID
        ↓
7. Action logged to audit trail
```

### Response Format (StandardResponse)

All API responses follow a standard envelope:

```json
{
  "success": true,
  "data": {
    "id": "assess_...",
    "system_id": "pas-x",
    "status": "PENDING"
  },
  "error": null,
  "trace_id": "uuid-string",
  "timestamp": "2026-08-27T10:00:00Z"
}
```

**Why this format**:
- Consistent across all endpoints
- Trace ID for debugging/auditing
- Timestamp for audit trail
- Clear success/error distinction
- Optional data payload

---

## IMPLEMENTED MODULES

### 1. API Framework (`backend/app/api/`)

**File**: `app.py`  
**Size**: ~350 lines  
**Purpose**: Flask application factory, route definitions, middleware

**Key endpoints**:
- `POST /api/v1/auth/login` - Authenticate user
- `POST /api/v1/auth/logout` - Logout user
- `POST /api/v1/assessment/start` - Create assessment
- `POST /api/v1/assessment/{id}/run` - Run assessment
- `GET /api/v1/assessment/{id}` - Get assessment metadata
- `GET /api/v1/assessment/{id}/findings` - Get findings
- `GET /api/v1/assessment/{id}/readiness` - Get readiness score
- `GET /api/v1/evidence/search` - Search evidence (FTS5)
- `GET /api/v1/user/profile` - Get current user
- `GET /api/v1/health` - Health check

**Decorators**:
- `@require_auth` - Verify Bearer token
- `@require_permission(action, resource)` - Check authorization
- `success_response(data, status)` - Return success response
- `error_response(message, status)` - Return error response

**Error handling**:
- 400: Bad request (missing/invalid data)
- 401: Authentication failed
- 403: Authorization failed
- 404: Resource not found
- 500: Server error

### 2. Authentication Service (`backend/app/services/auth_service.py`)

**Size**: ~150 lines  
**Purpose**: User authentication, token management, permission checking

**Methods**:
- `authenticate(username, password) -> str` - Login, return token
- `verify_token(token) -> User` - Verify token, return user
- `check_permission(user, action, resource) -> bool` - Check if user has permission
- `require_permission(user, action, resource) -> None` - Require permission or raise
- `logout(token) -> None` - Invalidate token

**Token flow**:
1. Client calls `POST /api/v1/auth/login` with username/password
2. AuthService hashes password, compares with stored hash
3. If match, generate random token, store with expiration
4. Return token to client
5. Client includes token in subsequent requests: `Authorization: Bearer <token>`
6. AuthService looks up token in database, verifies not expired
7. Returns associated User object

**Token storage**:
- Table: `tokens` (user_id, token, expires_at)
- TTL: 3600 seconds (1 hour)
- Lookup: O(1) SQL query

### 3. Assessment Service (`backend/app/services/assessment_service.py`)

**Size**: ~200 lines  
**Purpose**: Manage assessment lifecycle, orchestrate deterministic engine

**Methods**:
- `start_assessment(system_id, user_id) -> Assessment` - Create new assessment
- `run_assessment(assessment_id) -> List[Finding]` - Execute deterministic engine
- `get_assessment(assessment_id) -> Assessment` - Fetch metadata
- `get_findings(assessment_id) -> List[Finding]` - Fetch findings
- `get_readiness_score(assessment_id) -> ReadinessScore` - Calculate score
- `search_evidence(query) -> List` - FTS5 search

**Assessment lifecycle**:
1. Client: `POST /api/v1/assessment/start` → Assessment created in PENDING state
2. Client: `POST /api/v1/assessment/{id}/run` → Status changes to RUNNING
3. Service calls `ChecklistEngine.evaluate_all_controls()` (M0-M2 core)
4. Each Finding stored in database
5. Status changes to COMPLETE or FAILED
6. Results queryable via GET endpoints

**Key decision**: The deterministic engine owns all findings. The service layer orchestrates but does not alter.

### 4. Evidence Verifier (`backend/app/verification/evidence_verifier.py`)

**Size**: ~80 lines  
**Purpose**: Verify that findings are grounded in actual evidence

**Methods**:
- `verify_finding(finding) -> VerificationResult` - Verify single finding
- `verify_findings_batch(findings) -> dict` - Verify multiple findings

**Verification checks**:
1. Finding has at least one evidence reference
2. All evidence IDs exist in index
3. Evidence chunks are retrievable

**Purpose**: Prevent unsupported claims from becoming part of audit record. Every finding must reference actual indexed evidence.

### 5. Policy Gateway (`backend/app/policy/policy_gateway.py`)

**Size**: ~70 lines  
**Purpose**: Enforce organizational policies before actions execute

**Methods**:
- `evaluate_action(action_type, resource_type, user_id) -> PolicyDecision` - Evaluate policy
- `require_policy(action_type, resource_type, user_id) -> None` - Require policy or raise

**Policy checks**:
1. User exists in database
2. User has a role assigned
3. Role has permission for (action_type, resource_type) pair
4. If not, return PolicyDecision(allowed=False, reason="...")

**Example**:
```
PolicyGateway.evaluate_action(
    action_type="APPROVE_FINDING",
    resource_type="FINDING",
    user_id="user-123"
)
→ PolicyDecision(allowed=True)  # QA role can approve findings
```

### 6. Action Gateway (`backend/app/actions/action_gateway.py`)

**Size**: ~100 lines  
**Purpose**: Execute (mock) actions after human approval

**Methods**:
- `execute_approved_action(action_id, user_id, action_type, params)` - Execute action
- `dry_run_action(action_id, action_type, params)` - Preview action
- `reject_action(action_id, user_id, reason)` - Reject action

**For the prototype**:
- Actions are never executed against real systems
- They are logged to audit trail
- They are marked as completed
- This is sufficient for demonstration

**Example**:
```
ActionGateway.execute_approved_action(
    action_id="act-456",
    user_id="user-123",
    action_type="UPDATE_SOP",
    params={"control_id": "C-1.1", "revised_content": "..."}
)
→ ActionResult(success=True, message="Action logged (prototype: no real execution)")
→ Audit trail records: timestamp, user, action, params
```

---

## DATABASE SCHEMA (M3 Additions)

### Users Table

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role_id TEXT NOT NULL REFERENCES roles(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

### Roles Table

```sql
CREATE TABLE roles (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);
```

**Default roles**:
- `SYSTEM_OWNER` - Full access, can configure system
- `QA_REVIEWER` - Can review test evidence, approve
- `AUDITOR` - Can see all findings, approve for sign-off
- `LEADERSHIP_VIEWER` - Read-only access to dashboards
- `SECURITY_TESTER` - Can run Assurance Lab scenarios

### Permissions Table

```sql
CREATE TABLE permissions (
    role_id TEXT REFERENCES roles(id),
    action TEXT,
    resource TEXT,
    PRIMARY KEY (role_id, action, resource)
);
```

**Examples**:
- `(SYSTEM_OWNER, APPROVE_FINDING, FINDING)`
- `(QA_REVIEWER, APPROVE_FINDING, FINDING)`
- `(AUDITOR, SIGN_OFF, ASSESSMENT)`
- `(LEADERSHIP_VIEWER, VIEW, DASHBOARD)`

### Tokens Table

```sql
CREATE TABLE tokens (
    token TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Assessments Table

```sql
CREATE TABLE assessments (
    id TEXT PRIMARY KEY,
    system_id TEXT NOT NULL,
    user_id TEXT NOT NULL REFERENCES users(id),
    status TEXT DEFAULT 'PENDING',  -- PENDING, RUNNING, COMPLETE, FAILED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
```

### Findings Table

```sql
CREATE TABLE findings (
    id TEXT PRIMARY KEY,
    assessment_id TEXT NOT NULL REFERENCES assessments(id),
    control_id TEXT NOT NULL,
    finding TEXT NOT NULL,
    severity TEXT NOT NULL,  -- CRITICAL, HIGH, MEDIUM, LOW
    confidence TEXT NOT NULL,  -- VERY_HIGH, HIGH, MEDIUM, LOW
    evidence_refs TEXT,  -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Approvals Table

```sql
CREATE TABLE approvals (
    id TEXT PRIMARY KEY,
    finding_id TEXT NOT NULL REFERENCES findings(id),
    user_id TEXT NOT NULL REFERENCES users(id),
    decision TEXT NOT NULL,  -- APPROVED, REJECTED, CLARIFICATION_NEEDED
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Actions Table

```sql
CREATE TABLE actions (
    id TEXT PRIMARY KEY,
    approval_id TEXT REFERENCES approvals(id),
    action_type TEXT NOT NULL,
    params TEXT,  -- JSON
    status TEXT DEFAULT 'PENDING',  -- PENDING, APPROVED, REJECTED, EXECUTED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP
);
```

### Audit Trail Table

```sql
CREATE TABLE audit_trail (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP NOT NULL,
    user_id TEXT REFERENCES users(id),
    action_type TEXT NOT NULL,
    action_id TEXT,
    status TEXT,
    params TEXT,  -- JSON
    previous_hash TEXT,
    current_hash TEXT
);
```

**Hash chain**: Each audit event includes hash of previous event for tampering detection.

---

## TESTING STRATEGY FOR M3

### Unit Tests

Test each service in isolation with mocked database:

```python
def test_auth_service_authenticate():
    auth = AuthService(mock_db)
    token = auth.authenticate("user1", "password1")
    assert token is not None
    assert len(token) > 0

def test_assessment_service_start():
    service = AssessmentService(mock_db)
    assessment = service.start_assessment("pas-x", "user-123")
    assert assessment.status == AssessmentStatus.PENDING
    assert assessment.system_id == "pas-x"
```

### Integration Tests

Test API endpoints with real SQLite (in-memory) database:

```python
def test_api_health_check():
    client = create_app().test_client()
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    assert json.loads(response.data)['success'] == True

def test_api_requires_auth():
    client = create_app().test_client()
    response = client.post('/api/v1/assessment/start', json={'system_id': 'pas-x'})
    assert response.status_code == 401
```

### Authorization Tests

Verify that unauthorized roles get 403:

```python
def test_unauthorized_role_gets_403():
    # Create user with LEADERSHIP_VIEWER role
    # Try to POST to APPROVE_FINDING endpoint
    # Expect 403 Forbidden
```

### Audit Tests

Verify that actions are logged:

```python
def test_action_logged_to_audit_trail():
    service.start_assessment(...)
    audit = db.query("SELECT * FROM audit_trail ORDER BY timestamp DESC LIMIT 1")
    assert audit.action_type == "START_ASSESSMENT"
    assert audit.user_id == user_id
```

---

## M3 DELIVERABLES

### Code

- ✅ `backend/app/api/app.py` (350 lines)
- ✅ `backend/app/api/schemas/` (common.py, __init__.py)
- ✅ `backend/app/services/auth_service.py` (150 lines)
- ✅ `backend/app/services/assessment_service.py` (200 lines)
- ✅ `backend/app/services/__init__.py`
- ✅ `backend/app/verification/evidence_verifier.py` (80 lines)
- ✅ `backend/app/verification/__init__.py`
- ✅ `backend/app/policy/policy_gateway.py` (70 lines)
- ✅ `backend/app/policy/__init__.py`
- ✅ `backend/app/actions/action_gateway.py` (100 lines)
- ✅ `backend/app/actions/__init__.py`

### Tests

- ✅ `tests/integration/test_api_endpoints.py` (80+ lines)

### Documentation

- ✅ `docs/M3_SYSTEM_DESIGN.md` (this file)
- Required: `docs/API_SPECIFICATION.md` (full endpoint reference)
- Required: `docs/DATABASE_SCHEMA.md` (schema reference)

### Configuration

- ✅ `requirements.txt` (Flask 3.0.0 and dependencies)
- Required: Database migration script
- Required: Sample users/roles seed script

---

## M3 COMPLETION CHECKLIST

- [x] API framework (Flask application, routes, middleware)
- [x] Authentication service (login, token management, logout)
- [x] Authorization layer (check_permission, require_permission)
- [x] Assessment service (orchestrate deterministic engine)
- [x] Evidence verifier (claim grounding verification)
- [x] Policy gateway (organizational policy enforcement)
- [x] Action gateway (mock execution, dry-run, audit logging)
- [ ] Database schema (migration script)
- [ ] Database seed script (create demo users/roles)
- [ ] Integration tests (all endpoints tested)
- [ ] Authorization tests (403 responses verified)
- [ ] Audit trail tests (actions logged correctly)
- [ ] Documentation (API spec, database schema)
- [ ] Error handling (all error paths tested)
- [ ] Response validation (all responses follow StandardResponse)

---

## NEXT STEPS (M4+)

**M4**: Auditor Challenges (25 cross-record reconciliation rules)  
**M5**: Local AI Runtime (llama.cpp integration)  
**M6**: Agent Orchestration (A0-A7 implementation)  
**M7**: Evidence Graph (traceability and visualization)  
**M8**: Human Control (approval workflows, Trust Centre)  
**M9**: UI Implementation (9 workspaces)  
**M10**: Testing & Release (final validation, packaging)

---

*M3 System Design prepared: 27 August 2026*
