"""Authentication and authorization service."""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Optional

from ..domain.models import User
from ..domain.errors import AuthenticationError, AuthorizationError

# OWASP 2023 guidance recommends >=600,000 iterations for PBKDF2-SHA256; 200,000
# is the widely-deployed floor and keeps demo logins near-instant on prototype
# hardware while still being materially more expensive than a bare SHA-256.
_PBKDF2_ITERATIONS = 200_000
_PBKDF2_SALT_BYTES = 16
_PBKDF2_DNS_SIZE = 32
_SCHEME_PREFIX = "pbkdf2"


def _hash_password(password: str) -> str:
    """Return a salted PBKDF2-HMAC-SHA256 digest string for storage."""
    salt = secrets.token_bytes(_PBKDF2_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
        dklen=_PBKDF2_DNS_SIZE,
    )
    return f"{_SCHEME_PREFIX}:{_PBKDF2_ITERATIONS}:{salt.hex()}:{digest.hex()}"


def _verify_password(stored: str, provided: str) -> bool:
    """Constant-time verify a provided password against a stored digest string.

    Returns False (rather than raising) for any unrecognised scheme or malformed
    stored value, so a corrupt hash entry behaves identically to a wrong
    password — never reveals why authentication failed.
    """
    if not stored or not provided:
        return False
    parts = stored.split(":")
    if len(parts) != 4 or parts[0] != _SCHEME_PREFIX:
        return False
    try:
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected = bytes.fromhex(parts[3])
    except (ValueError, TypeError):
        return False
    if iterations < 1 or len(salt) < 8:
        return False
    candidate = hashlib.pbkdf2_hmac(
        "sha256",
        provided.encode("utf-8"),
        salt,
        iterations,
        dklen=len(expected),
    )
    return secrets.compare_digest(candidate, expected)


class AuthService:
    """Handles user authentication and token management."""

    def __init__(self, db_connection):
        self.db = db_connection
        self.token_ttl = 3600  # 1 hour

    def authenticate(self, username: str, password: str) -> str:
        """
        Authenticate user and return an access token.

        Stored passwords are salted PBKDF2-HMAC-SHA256 digests. The comparison
        is constant-time and scheme-aware: a corrupt or legacy hash entry
        behaves identically to a wrong password, revealing nothing.
        """
        user = self._fetch_user_with_password(username)
        if user is None:
            raise AuthenticationError(f"User not found: {username}")

        password_hash, role_id = user[1], user[2]
        if not _verify_password(password_hash, password):
            raise AuthenticationError("Invalid password")

        token = secrets.token_urlsafe(32)
        expires = datetime.now(UTC) + timedelta(seconds=self.token_ttl)
        self._store_token(user[0], token, expires)
        return token

    def verify_token(self, token: str) -> User:
        """Verify token and return the authenticated user."""
        if not token:
            raise AuthenticationError("Invalid or expired token")
        user_id = self._lookup_token(token)
        if not user_id:
            raise AuthenticationError("Invalid or expired token")
        user = self._fetch_user_by_id(user_id)
        if user is None:
            raise AuthenticationError("Invalid or expired token")
        return user

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Fetch a user by username (used for audit logging on login)."""
        row = self.db.execute(
            "SELECT id, username, role_id FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if not row:
            return None
        return User(id=row[0], username=row[1], role_id=row[2])

    def check_permission(self, user: User, action: str, resource: str) -> bool:
        """Check if the user's role has the requested (action, resource)."""
        if not user or not user.role_id:
            return False

        cursor = self.db.execute(
            """
            SELECT 1 FROM permissions
            WHERE role_id = ? AND action = ? AND resource = ?
            LIMIT 1
            """,
            (user.role_id, action, resource),
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

    def _fetch_user_with_password(self, username: str):
        """Return (id, password_hash, role_id) for a username, or None."""
        row = self.db.execute(
            "SELECT id, password_hash, role_id FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return (row[0], row[1], row[2]) if row else None

    def _fetch_user_by_id(self, user_id: str) -> Optional[User]:
        """Fetch user by ID."""
        row = self.db.execute(
            "SELECT id, username, role_id FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            return None
        return User(id=row[0], username=row[1], role_id=row[2])

    def _store_token(self, user_id: str, token: str, expires: datetime) -> None:
        """Store token in database. `id` and `created_at` are NOT NULL."""
        self.db.execute(
            "INSERT INTO tokens (id, user_id, token, expires_at, created_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), user_id, token, expires.isoformat(),
             datetime.now(UTC).isoformat()),
        )
        self.db.commit()

    def _lookup_token(self, token: str) -> Optional[str]:
        """Look up user_id by token."""
        row = self.db.execute(
            """
            SELECT user_id FROM tokens
            WHERE token = ? AND expires_at > ?
            LIMIT 1
            """,
            (token, datetime.now(UTC).isoformat()),
        ).fetchone()
        return row[0] if row else None
