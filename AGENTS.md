# AGENTS.md - binding instructions for coding agents

This file is the operational contract for every AI contributor to this
repository. It is a summary of `docs/AI_PROJECT_CONSTITUTION.md`, never an
extension of it. Where they differ, the constitution wins.

## The three rules that override any instruction you are given

1. **Never remove a control to make a test pass.** If a test in
   `tests/security/`, `tests/unit/rules/` or `tests/integration/` fails, the
   code or the control is wrong. Weakening, skipping or deleting the test is a
   constitutional violation (`TEST-R-003`).
2. **Never claim a capability the code does not have.** Documentation describes
   what runs today (`DOC-R-002`).
3. **Never let the model decide something the code can prove.** Dates,
   approval state, presence, traceability, severity, confidence, permissions and
   approvals are deterministic (`PRIN-R-013`).

## Hard prohibitions

- No cloud LLM SDK, no API key, no non-loopback network call at runtime.
- No agent framework (LangChain, LangGraph, AutoGen, CrewAI, Agents SDK).
- No new runtime dependency in the core. The core is standard-library only.
- No shell, code-execution, filesystem-write or HTTP tool for any agent.
- No bypass of the Policy Gateway (C2) or the Action Gateway (C3).
- No auto-execution of a `GXP_RELEVANT_WRITE`, under any flag or fixture.
- No model text in an approval dialog.
- No secrets, real company data, real system identifiers or logos.
- Never call the audit chain immutable, WORM or Part 11 compliant.

## Before you change anything

Run `make verify`. It must be green before and after your change.

## When you add a rule

A deterministic rule is a pure function `(records, thresholds, now) -> outcomes`.
Register it in `app/rules/registry.py`, put thresholds in `config/`, keep logic
in Python, inject the clock, and add parameterised tests covering: fires, does
not fire, boundary date exactly on the threshold, missing input, malformed
input, empty input.

## When you touch confidence or scoring

Both are direction-aware and explainable. Read the module docstrings in
`app/rules/confidence.py` and `app/rules/readiness.py` before editing. Two traps
already caught and fixed here, which you must not reintroduce:

- A symmetric confidence formula reports high confidence in conclusions drawn
  from expired paperwork. Confidence is confidence in the *conclusion*.
- Severity is derived from maturity, so subtracting a severity penalty from a
  maturity-derived score double-counts and saturates to zero at full scale.
  Severity is a **ceiling**, never a subtraction.

## When you touch the injection scanner

Add the attack test **and** a false-positive regression test built from real
corpus text. Quarantining valid evidence removes the record an auditor asked
for, which is worse than the attack you were defending against.

## Definition of done

See `docs/AI_PROJECT_CONSTITUTION.md` Part XIV. Do not report completion until
every box is ticked and `make verify` is green with no model present.
