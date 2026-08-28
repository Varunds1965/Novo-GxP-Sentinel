# API Specification

**PROTOTYPE - SYNTHETIC DATA - NOT VALIDATED FOR PRODUCTION GxP USE**
*Not a compliance certification.*

## Server

- Host: `127.0.0.1`
- Port: `8765`
- Protocol: HTTP (prototype only; production requires TLS)
- Base URL: `http://127.0.0.1:8765/api/v1`

## Authentication

All protected endpoints require:
```
Authorization: Bearer <token>
```

Token obtained via `/auth/login`.

## Response Envelope

All responses include:

```json
{
  "success": true|false,
  "data": { ... } or null,
  "error": "error message" or null,
  "trace_id": "uuid",
  "timestamp": "2026-08-28T10:30:00Z"
}
```

HTTP status codes:
- 200: OK
- 201: Created
- 400: Bad request
- 401: Unauthorized (missing/invalid token)
- 403: Forbidden (authorized user lacks permission)
- 404: Not found
- 500: Internal error
- 501: Not implemented

## Endpoints

### Authentication

#### POST /api/v1/auth/login

Request:
```json
{ "username": "user", "password": "pass" }
```

Response (200):
```json
{
  "success": true,
  "data": {
    "access_token": "token",
    "token_type": "bearer",
    "expires_in": 3600
  },
  ...
}
```

#### POST /api/v1/auth/logout

Required auth: Yes

Response (200): `{ "message": "Logged out" }`

### Assessment

#### POST /api/v1/assessment/start

Required auth: Yes
Required permission: `PROPOSE` on `ASSESSMENT`

Request:
```json
{ "system_id": "NL-MES-001" }
```

Response (201):
```json
{
  "id": "asmt-uuid",
  "system_id": "NL-MES-001",
  "status": "PENDING",
  "created_at": "2026-08-28T..."
}
```

#### POST /api/v1/assessment/{id}/run

Required auth: Yes
Required permission: `PROPOSE` on `ASSESSMENT`

Response (200):
```json
{
  "assessment_id": "...",
  "findings_count": 169,
  "status": "COMPLETE"
}
```

#### GET /api/v1/assessment/{id}

Required auth: Yes
Required permission: `READ` on `ASSESSMENT`

Response (200): Assessment object

#### GET /api/v1/assessment/{id}/findings

Required auth: Yes
Required permission: `READ` on `ASSESSMENT`

Response (200):
```json
{
  "assessment_id": "...",
  "findings": [ { "id": "...", "severity": "HIGH", ... } ],
  "total": 169
}
```

#### GET /api/v1/assessment/{id}/readiness

Required auth: Yes
Required permission: `READ` on `ASSESSMENT`

Response (200):
```json
{
  "assessment_id": "...",
  "readiness_score": 29,
  "status": "NOT_READY_FOR_INSPECTION"
}
```

### Evidence

#### GET /api/v1/evidence/search

Required auth: Yes
Required permission: `READ` on `EVIDENCE`

Query params: `q=<search term>`

Response (200):
```json
{
  "query": "backup",
  "results": [ { "source_id": "...", "title": "..." } ],
  "count": 5
}
```

#### POST /api/v1/evidence/upload

Required auth: Yes
Required permission: `INGEST` on `EVIDENCE`

Status: `NOT_YET_IMPLEMENTED` (501)

### User

#### GET /api/v1/user/profile

Required auth: Yes

Response (200):
```json
{
  "id": "user-uuid",
  "username": "alice",
  "role_id": "SYSTEM_OWNER"
}
```

### Health

#### GET /api/v1/health

Public (no auth required)

Response (200):
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0"
}
```

### Copilot (M5 - stub)

#### POST /api/v1/copilot/ask

Status: `NOT_YET_IMPLEMENTED` (501)

### Graph (M7 - stub)

#### GET /api/v1/graph/nodes

Status: `NOT_YET_IMPLEMENTED` (501)

### Approvals (M8 - stub)

#### GET /api/v1/approvals

Status: `NOT_YET_IMPLEMENTED` (501)

#### POST /api/v1/approvals/{id}/decide

Status: `NOT_YET_IMPLEMENTED` (501)

### Assurance Lab (M8 - stub)

#### POST /api/v1/assurance-lab/scenario/{id}/run

Status: `NOT_YET_IMPLEMENTED` (501)

## Permission Model

Five roles with granular action/resource permissions:

| Role | READ | INGEST | PROPOSE | APPROVE | RUN_LAB |
|---|---|---|---|---|---|
| SYSTEM_OWNER | Yes | Yes | Yes | Yes | Yes |
| QA_REVIEWER | Yes | No | Yes | Yes | No |
| AUDITOR | Yes | No | No | No | No |
| LEADERSHIP_VIEWER | Yes | No | No | No | No |
| SECURITY_TESTER | Yes | No | No | No | Yes |

## Error Responses

All errors follow the envelope:

```json
{
  "success": false,
  "error": "error description",
  "trace_id": "uuid",
  "timestamp": "..."
}
```

Common errors:
- 401: `"Missing authentication token" / "Invalid or expired token"`
- 403: `"User <id> not authorized for <action> on <resource>"`
- 404: `"Not found"`
- 500: `"Internal server error"`
- 501: `"Not yet implemented"`
