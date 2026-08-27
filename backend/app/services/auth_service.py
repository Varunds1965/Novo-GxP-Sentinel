"""Authentication and authorization service."""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

from ..domain.models import User, Role
from ..domain.errors import AuthenticationError, AuthorizationError


class AuthService:
    """Handles user authentication and token management."""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.token_secret = secrets.token_hex(32)
        self.token_ttl = 3600  # 1 hour
    
    def authenticate(self, username: str, password: str) -> str:
        """
        Authenticate user and return access token.
        
        In a prototype, password hashing is simple. In production,
        use bcrypt/argon2 and implement proper password policies.
        """
        user = self._fetch_user(username)
        if not user:
            raise AuthenticationError(f"User not found: {username}")
        
        # Simple hash: in production use bcrypt
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        user_password_hash = hashlib.sha256(user.password_hash.encode()).hexdigest()
        
        if password_hash != user_password_hash:
            raise AuthenticationError("Invalid password")
        
        # Generate token
        token = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(seconds=self.token_ttl)
        
        # Store token in database
        self._store_token(user.id, token, expires)
        
        return token
    
    def verify_token(self, token: str) -> Optional[User]:
        """Verify token and return associated user."""
        user_id = self._lookup_token(token)
        if not user_id:
            raise AuthenticationError("Invalid or expired token")
        
        user = self._fetch_user_by_id(user_id)
        return user
    
    def check_permission(self, user: User, action: str, resource: str) -> bool:
        """Check if user has permission for action on resource."""
        if not user or not user.role:
            return False
        
        # Query permissions table
        cursor = self.db.execute(
            """
            SELECT 1 FROM permissions
            WHERE role_id = ? AND action = ? AND resource = ?
            LIMIT 1
            """,
            (user.role.id, action, resource)
        )
        
        return cursor.fetchone() is not None
    
    def require_permission(self, user: User, action: str, resource: str) -> None:
        """Require permission or raise AuthorizationError."""
        if not self.check_permission(user, action, resource):
            raise AuthorizationError(
                f"User {user.id} not authorized for {action} on {resource}"
            )
    
    def logout(self, token: str) -> None:
        """Invalidate token."""
        self.db.execute("DELETE FROM tokens WHERE token = ?", (token,))
        self.db.commit()
    
    # Private methods
    
    def _fetch_user(self, username: str) -> Optional[User]:
        """Fetch user by username."""
        cursor = self.db.execute(
            "SELECT id, username, role_id FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return User(id=row[0], username=row[1], role_id=row[2])
    
    def _fetch_user_by_id(self, user_id: str) -> Optional[User]:
        """Fetch user by ID."""
        cursor = self.db.execute(
            "SELECT id, username, role_id FROM users WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return User(id=row[0], username=row[1], role_id=row[2])
    
    def _store_token(self, user_id: str, token: str, expires: datetime) -> None:
        """Store token in database."""
        self.db.execute(
            "INSERT INTO tokens (user_id, token, expires_at) VALUES (?, ?, ?)",
            (user_id, token, expires.isoformat())
        )
        self.db.commit()
    
    def _lookup_token(self, token: str) -> Optional[str]:
        """Look up user_id by token."""
        cursor = self.db.execute(
            """
            SELECT user_id FROM tokens
            WHERE token = ? AND expires_at > ?
            LIMIT 1
            """,
            (token, datetime.utcnow().isoformat())
        )
        row = cursor.fetchone()
        return row[0] if row else None
