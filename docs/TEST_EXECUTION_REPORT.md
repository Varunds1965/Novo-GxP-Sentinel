# Test Execution Report

**TEMPLATE - Run on Windows to populate with actual results**

**Report date:** (To be filled in by Windows execution)
**Environment:** Windows 10/11, PowerShell
**Python version:** (To be filled)
**OS:** (To be filled)

## Execution Command

```powershell
cd C:\Users\Varun\Documents\GitHub\Novo-GxP-Sentinel
.venv\Scripts\Activate.ps1
$env:PYTHONPATH="backend"
pytest -v --junitxml=docs/evidence/pytest-results.xml 2>&1 | Tee-Object -FilePath docs/evidence/pytest-output.txt
```

## Test Results

### Summary

| Metric | Count | Status |
|---|---|---|
| Total | **[ACTUAL: run pytest]** | |
| Passed | **[ACTUAL]** | |
| Failed | **[ACTUAL]** | |
| Errors | **[ACTUAL]** | |
| Skipped | **[ACTUAL]** | |
| Duration | **[ACTUAL]** | |

### Test Details

Paste the full pytest output below:

```
[PASTE FULL PYTEST OUTPUT HERE]
```

### Failures (if any)

For each failure, record:

**Test:** test_name
**Failure reason:** (from pytest output)
**Root cause:** (from investigation)
**Fix applied:** (if resolved)
**Rerun result:** PASS / FAIL

## Execution Status

- [ ] Database initialized successfully
- [ ] All dependencies available
- [ ] No import errors
- [ ] Health check endpoint accessible
- [ ] Authentication test passed
- [ ] Authorization test passed
- [ ] At least 7 of 8 tests passed (expected baseline)

## Known Issues Encountered

List any issues not already documented:

- Issue: [description]
  - Diagnosis: [root cause]
  - Resolution: [action taken or workaround]

## Assessment Baseline Re-run

After tests pass, re-run the baseline assessment to confirm readiness is still 29/100:

```powershell
.\RUN_ASSESSMENT.bat
cat docs/evidence/assessment.json | jq .readiness_score
```

Expected result: `29` (unchanged)

If different, investigate why:
- Did baseline evidence change?
- Was baseline evidence improved (violates test integrity rule)?
- Are findings genuinely different?

Document any variance from 29/100 with root cause.

## Verification Checklist

- [ ] All 8 test files found by pytest
- [ ] No test was deleted or skipped in the codebase to make results look better
- [ ] All failures have root causes documented
- [ ] Readiness baseline is still 29/100 (or variance explained)
- [ ] No synthetic data is presented as company evidence
- [ ] Audit trail integration confirms all action logging works
- [ ] Authorization boundaries are enforced at API level

## Sign-Off

Windows execution completed by: [Your name / date]
Results match or explain variance from expectations: [Yes / No]
No test integrity violations: [Yes / No]
