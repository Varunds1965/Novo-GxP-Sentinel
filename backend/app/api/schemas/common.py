"""Common API schemas for all endpoints."""

from dataclasses import dataclass
from typing import Optional, Any
from datetime import datetime
import uuid


@dataclass
class StandardResponse:
    """Universal API response envelope."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    trace_id: str = ""
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.trace_id:
            self.trace_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat() + "Z"


@dataclass
class TokenResponse:
    """Authentication response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


@dataclass
class UserDTO:
    """User data transfer object."""
    id: str
    username: str
    role: str
    created_at: str


@dataclass
class RoleDTO:
    """Role information."""
    id: str
    name: str


@dataclass
class PermissionDTO:
    """Permission information."""
    action: str
    resource: str
