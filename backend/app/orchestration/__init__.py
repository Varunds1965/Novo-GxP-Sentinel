"""Bounded agent orchestration (M6 supporting layer).

STATUS: STUB - orchestration engine not yet implemented.

When implemented, this module enforces safety constraints on agentic loops:
- Maximum turns per orchestration session
- Maximum tool calls per agent
- Maximum runtime (wall-clock and CPU)
- Recursion detection and termination
- Graceful cancellation
- Resource cleanup

All agent decisions must pass through:
1. Policy gateway (app/policy/policy_gateway.py)
2. Action gateway (app/actions/action_gateway.py)
3. RBAC check
4. Approval requirement check (if GxP-relevant)
5. Audit logging

No agent can bypass this chain. Orchestration enforces it at the call site.
"""
