"""
Action Gateway: Execute (mock) actions with human approval.

For the prototype, actions are never executed against real systems.
They are logged to the audit trail and marked as completed.
This is sufficient for demonstration purposes.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ActionResult:
    """Result of action execution."""
    success: bool
    message: str
    action_id: str = ""
    executed_at: Optional[str] = None


class ActionGateway:
    """Execute (mock) actions after approval."""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def execute_approved_action(self, action_id: str, user_id: str,
                               action_type: str, params: dict) -> ActionResult:
        """
        Execute an action that has been approved by a human.
        
        For the prototype, this is always a mock action.
        Real GxP changes are never made automatically.
        """
        
        # Log to audit trail
        self._log_action(action_id, user_id, action_type, params, "APPROVED")
        
        # For prototype: mark as executed but do nothing real
        return ActionResult(
            success=True,
            message=f"Action {action_type} logged (prototype: no real execution)",
            action_id=action_id,
            executed_at=datetime.utcnow().isoformat(),
        )
    
    def dry_run_action(self, action_id: str, action_type: str, 
                      params: dict) -> ActionResult:
        """
        Show what an action would do without executing it.
        
        Used for preview before approval.
        """
        
        prediction = self._predict_action_effect(action_type, params)
        
        return ActionResult(
            success=True,
            message=f"Dry run: {prediction}",
            action_id=action_id,
        )
    
    def reject_action(self, action_id: str, user_id: str, reason: str) -> ActionResult:
        """Reject an action."""
        
        self._log_action(action_id, user_id, "REJECTION", 
                        {"reason": reason}, "REJECTED")
        
        return ActionResult(
            success=True,
            message=f"Action rejected: {reason}",
            action_id=action_id,
        )
    
    # Private methods
    
    def _log_action(self, action_id: str, user_id: str, action_type: str,
                   params: dict, status: str) -> None:
        """Log action to audit trail."""
        import json
        self.db.execute(
            """
            INSERT INTO audit_trail 
            (timestamp, user_id, action_type, action_id, status, params)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (datetime.utcnow().isoformat(), user_id, action_type, 
             action_id, status, json.dumps(params))
        )
        self.db.commit()
    
    def _predict_action_effect(self, action_type: str, params: dict) -> str:
        """Predict what an action would do."""
        effects = {
            'APPROVE_EVIDENCE': f"Mark evidence as approved: {params.get('evidence_id')}",
            'UPDATE_SOP': f"Draft revised SOP for control: {params.get('control_id')}",
            'ESCALATE_INCIDENT': f"Escalate incident: {params.get('incident_id')}",
            'ASSIGN_REMEDIATION': f"Assign to: {params.get('assignee')}",
        }
        
        return effects.get(action_type, f"Execute {action_type}")
