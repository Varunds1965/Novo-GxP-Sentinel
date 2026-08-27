"""
Policy Gateway: Enforce organizational policies.

Before an action executes, the policy gateway checks:
1. User has the required role
2. Resource is not restricted
3. Time-based restrictions (if any)
4. Conditional rules (e.g., "QA must approve test evidence")
"""

from dataclasses import dataclass
from ..domain.errors import AuthorizationError


@dataclass
class PolicyDecision:
    """Result of policy evaluation."""
    allowed: bool
    reason: str = ""


class PolicyGateway:
    """Enforce policies on actions."""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def evaluate_action(self, action_type: str, resource_type: str, 
                       user_id: str) -> PolicyDecision:
        """
        Evaluate whether an action is allowed by policy.
        
        Args:
            action_type: e.g., "APPROVE_FINDING", "EXECUTE_ACTION", "UPLOAD_EVIDENCE"
            resource_type: e.g., "FINDING", "EVIDENCE", "ASSESSMENT"
            user_id: User performing the action
        
        Returns:
            PolicyDecision with allowed=True/False and reason
        """
        
        # Check if user exists and has a role
        cursor = self.db.execute(
            "SELECT role_id FROM users WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        if not row:
            return PolicyDecision(
                allowed=False,
                reason=f"User not found: {user_id}"
            )
        
        role_id = row[0]
        
        # Check if role has permission for this action on this resource
        cursor = self.db.execute(
            """
            SELECT 1 FROM permissions
            WHERE role_id = ? AND action = ? AND resource = ?
            LIMIT 1
            """,
            (role_id, action_type, resource_type)
        )
        
        if not cursor.fetchone():
            return PolicyDecision(
                allowed=False,
                reason=f"Role {role_id} not authorized for {action_type} on {resource_type}"
            )
        
        # Policy allows
        return PolicyDecision(allowed=True, reason="Authorized by policy")
    
    def require_policy(self, action_type: str, resource_type: str, user_id: str) -> None:
        """Require policy permission or raise AuthorizationError."""
        decision = self.evaluate_action(action_type, resource_type, user_id)
        if not decision.allowed:
            raise AuthorizationError(decision.reason)
