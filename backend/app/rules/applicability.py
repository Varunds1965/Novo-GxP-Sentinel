"""Lifecycle-phase applicability gating.

The single most important correction in the deterministic engine. A control
question for a lifecycle phase the system has not reached is NOT a gap: a system
in implementation has no decommissioning records, and it should not have any.
Reporting seventeen critical retirement findings against a pre-release MES would
be a false-positive cluster large enough to discredit every true finding beside
it, which is the fastest way for an assurance tool to lose a reviewer's trust.

The master SOP already supplies the correct vocabulary for this: the audit-agent
answer contract includes "Not applicable with evidence" as a distinct conclusion
from "Not demonstrated". This module decides which of the two applies, states the
evidence-based reason, and excludes not-yet-reached controls from the readiness
denominator while still reporting them.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.enums import Applicability, LifecycleState

# Checklist phase -> the lifecycle state a system must have reached for the
# phase to be assessable. Phases map onto the 14 auditable stages of the SOP.
PHASE_REQUIRES: dict[int, int] = {
    1: 1,   # Concept & business case
    2: 2,   # User requirements
    3: 3,   # Risk assessment & GAMP categorisation
    4: 4,   # Supplier assessment
    5: 5,   # Functional / design specifications
    6: 6,   # Configuration & development
    7: 7,   # Installation qualification
    8: 8,   # Operational qualification
    9: 9,   # Performance qualification / UAT
    10: 10,  # Go-live, release & handover
    11: 11,  # Operations & periodic review
    12: 12,  # Change & configuration management
    13: 13,  # Incident, problem & deviation management
    14: 14,  # Decommissioning, retention & migration
}

PHASE_NAMES: dict[int, str] = {
    1: "Concept & Business Case",
    2: "User Requirements (URS)",
    3: "Risk Assessment & GAMP Categorisation",
    4: "Supplier Assessment & Qualification",
    5: "Functional / Design Specifications",
    6: "Configuration & Development",
    7: "Installation Qualification (IQ)",
    8: "Operational Qualification (OQ)",
    9: "Performance Qualification (PQ) / UAT",
    10: "Go-Live, Release & Handover",
    11: "Operations & Periodic Review",
    12: "Change & Configuration Management",
    13: "Incident, Problem & Deviation Management",
    14: "Decommissioning, Data Retention & Migration",
}


@dataclass(frozen=True, slots=True)
class SystemLifecyclePosition:
    """Where a system actually is, derived from the evidence that exists."""

    state: LifecycleState
    highest_phase_reached: int
    basis: str

    def assess(self, phase_no: int) -> tuple[Applicability, str]:
        if phase_no <= self.highest_phase_reached:
            return Applicability.APPLICABLE, ""
        return (
            Applicability.NOT_YET_REACHED,
            (
                f"{PHASE_NAMES.get(phase_no, f'phase {phase_no}')} controls are not "
                f"assessable because the system is at "
                f"{PHASE_NAMES.get(self.highest_phase_reached, 'an earlier phase')} "
                f"({self.state.value}). {self.basis}"
            ),
        )


# Document types that evidence arrival at each checklist phase. Presence of the
# artefact is what proves the phase was entered; nothing is inferred from dates.
PHASE_MARKERS: dict[int, frozenset[str]] = {
    1: frozenset({"MLGP", "SYS"}),
    2: frozenset({"URS", "URR"}),
    3: frozenset({"ITRA", "ITRRA"}),
    4: frozenset({"SUPA", "SLA"}),
    5: frozenset({"FS", "DS", "DRR", "IS"}),
    6: frozenset({"CS", "AG"}),
    7: frozenset({"IQP", "IQTC", "IQR"}),
    8: frozenset({"OQP", "OQR", "OQTC"}),
    9: frozenset({"PQP", "PQR", "UAT"}),
    10: frozenset({"GOLIVE", "HANDOVER", "RELEASE"}),
    11: frozenset({"OMSOP_EXECUTED", "PSE_EXECUTED"}),
    12: frozenset({"CHG_EXECUTED"}),
    13: frozenset({"INC_EXECUTED", "DEVL_EXECUTED"}),
    14: frozenset({"RETIRE", "ARCHIVE", "DESTRUCTION"}),
}


def derive_position(document_types: frozenset[str]) -> SystemLifecyclePosition:
    """Determine the highest contiguously-evidenced phase.

    Contiguity matters: an artefact from a later phase does not prove the earlier
    gates were passed, and a package may legitimately contain forward-looking
    drafts. The scan therefore stops at the first phase with no marker present.
    """
    highest = 0
    for phase in sorted(PHASE_MARKERS):
        if PHASE_MARKERS[phase] & document_types:
            highest = phase
        else:
            break

    if highest >= 11:
        state = LifecycleState.OPERATE
    elif highest >= 5:
        state = LifecycleState.IMPLEMENT
    elif highest >= 1:
        state = LifecycleState.ANALYSE
    else:
        state = LifecycleState.ANALYSE

    reached = [PHASE_NAMES[p] for p in sorted(PHASE_MARKERS) if p <= highest]
    basis = (
        "Evidence of arrival was found for: " + "; ".join(reached) + "."
        if reached
        else "No phase-entry artefact was located in the indexed corpus."
    )
    return SystemLifecyclePosition(state=state, highest_phase_reached=highest, basis=basis)
