"""Bounded agents for GxP Sentinel (M6).

STATUS: IMPLEMENTATION BLOCKED - requires M5 (RAG/Copilot) foundation.

When implemented, this module will define:
- A0 Supervisor: orchestrates other agents
- A1 Knowledge: RAG-based evidence queries
- A2 Audit: checklist evaluation
- A3 Risk: risk assessment
- A4 Change Control: change evaluation
- A5 Incident: incident analysis
- A6 Access Control: access review
- A7 Remediation: remediation recommendation

Each agent:
- Has bounded input/output contracts
- Respects RBAC permissions
- Logs to audit trail
- Cannot bypass approval workflow
- Operates within recursion/tool/time budgets

See docs/AGENT_SPECIFICATION.md for detailed design.
"""
