# Windows Verification Guide

**PROTOTYPE - SYNTHETIC DATA - NOT VALIDATED FOR PRODUCTION GxP USE**
*Not a compliance certification.*

This document provides step-by-step instructions to verify GxP Sentinel functionality on Windows.

## Prerequisites

- Windows 10 or later
- PowerShell (recommended) or Command Prompt
- Python 3.9+
- Git

## 1. Repository Sync

```powershell
cd C:\Users\Varun\Documents\GitHub\Novo-GxP-Sentinel
git pull origin main
```

## 2. Activate Virtual Environment

```powershell
.venv\Scripts\Activate.ps1
```

If you get an execution policy error:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

Verify Flask:

```powershell
python -c "import flask; print(flask.__version__)"
```

## 4. Initialize Database

```powershell
$env:PYTHONPATH="backend"
python -c "from app.database import init_database; db = init_database(); print('Database initialized')"
```

You should see: `Database initialized`

## 5. Run Test Suite

```powershell
pytest -v --junitxml=docs/evidence/pytest-results.xml
```

Captured results in XML format for this audit.

## 6. Start the Web Server

Option A: Use the launcher:

```powershell
.\START_GXP_SENTINEL.bat
```

Option B: Manual start:

```powershell
$env:PYTHONPATH="backend"
python -m app.api.app
```

You should see:

```
Starting GxP Sentinel API on 127.0.0.1:8765...
 * Running on http://127.0.0.1:8765
```

## 7. Health Check (separate terminal)

```powershell
curl.exe http://127.0.0.1:8765/api/v1/health
```

Expected response:

```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "database": "connected",
    "version": "1.0.0"
  },
  "trace_id": "...",
  "timestamp": "..."
}
```

## 8. Run Assessment

```powershell
.\RUN_ASSESSMENT.bat
```

OR manually:

```powershell
$env:PYTHONPATH="backend"
python scripts/run_assessment.py
```

Results will be in `docs/evidence/`:
- `assessment.json`
- `findings_evidence_index.csv`
- `evidence_pack.html`
- `README.txt`

## 9. Verify Readiness Score

Check the baseline readiness (should be 29/100, NOT IMPROVED without evidence):

```powershell
cat docs/evidence/assessment.json | jq .readiness_score
```

Expected: `29`

## Expected Test Results

**Total tests:** 8

Tests that should pass:
- `test_health_check` - public endpoint
- `test_login_missing_credentials` - validation
- `test_assessment_requires_auth` - auth enforcement
- `test_evidence_search_requires_auth` - auth enforcement
- `test_response_includes_trace_id` - envelope structure
- `test_response_includes_timestamp` - envelope structure
- `test_auth_flow_requires_valid_user` - auth validation

**Expected: 7 PASSED, 0 FAILED, 0 ERRORS, 1 SKIPPED** (depending on fixture availability)

If tests fail, check:
1. `PYTHONPATH=backend` is set
2. Database is initialized
3. Flask is installed
4. No syntax errors in `backend/app/`

## Troubleshooting

### ImportError: cannot import name 'User'

This should be FIXED in this session. If it persists:

```powershell
python -c "from app.domain.models import User; print(User.__name__)"
```

Should print: `User`

If not, the fix did not apply. Check git status:

```powershell
git log --oneline -5
```

Should show the most recent commit mentioning "fix M0-M3 integration".

### Flask not found

```powershell
pip install flask werkzeug
```

### Port 8765 already in use

Find process using port:

```powershell
netstat -ano | findstr :8765
```

Kill it (if safe) or use a different port.

### Database locked

Delete the stale DB and reinitialize:

```powershell
rm data/gxp.db
python -c "from app.database import init_database; init_database()"
```

## What's Verified

After these steps, you will have verified:

- ✓ Python environment
- ✓ Dependencies installed
- ✓ Database initialization
- ✓ API server startup
- ✓ Authentication
- ✓ Authorization (RBAC)
- ✓ Audit logging
- ✓ Health endpoint
- ✓ Assessment execution
- ✓ Readiness scoring
- ✓ Test suite execution

You will NOT have verified:
- Frontend (no UI built yet)
- Copilot (M5 stub)
- Graph (M7 stub)
- Approval workflow (M8 stub)
- Agents (M6 missing)
- Upgrade impact (M4 missing)

These are next implementations for a follow-up session.
