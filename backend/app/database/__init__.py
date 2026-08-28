"""Database initialization and connection management.

Handles idempotent schema creation and per-request connection scoping.
"""

import sqlite3
import os
from pathlib import Path


def get_schema_sql() -> str:
    """Return the complete DDL schema."""
    return """
-- Users and authentication
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

CREATE TABLE IF NOT EXISTS roles (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS tokens (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    token TEXT UNIQUE NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Permissions matrix
CREATE TABLE IF NOT EXISTS permissions (
    id TEXT PRIMARY KEY,
    role_id TEXT NOT NULL,
    action TEXT NOT NULL,
    resource TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    UNIQUE(role_id, action, resource)
);

-- Evidence management
CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY,
    source_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    document_type TEXT NOT NULL,
    system_id TEXT NOT NULL,
    version TEXT NOT NULL,
    approval_status TEXT NOT NULL,
    trust_level TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    source_system TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    effective_date TEXT,
    review_date TEXT,
    owner TEXT,
    confidentiality TEXT,
    byte_size INTEGER DEFAULT 0,
    page_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS evidence_chunks (
    id TEXT PRIMARY KEY,
    evidence_id TEXT NOT NULL,
    chunk_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    location TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (evidence_id) REFERENCES evidence(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS evidence_injection_findings (
    id TEXT PRIMARY KEY,
    evidence_id TEXT NOT NULL,
    finding TEXT NOT NULL,
    severity TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (evidence_id) REFERENCES evidence(id) ON DELETE CASCADE
);

-- Assessments
CREATE TABLE IF NOT EXISTS assessments (
    id TEXT PRIMARY KEY,
    system_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    mode TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS findings (
    id TEXT PRIMARY KEY,
    assessment_id TEXT NOT NULL,
    control_id TEXT NOT NULL,
    finding TEXT NOT NULL,
    severity TEXT NOT NULL,
    confidence TEXT NOT NULL,
    evidence_refs TEXT,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS readiness_scores (
    id TEXT PRIMARY KEY,
    assessment_id TEXT NOT NULL,
    overall_score INTEGER NOT NULL,
    status TEXT NOT NULL,
    dimensions TEXT,
    computed_at TEXT NOT NULL,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
);

-- Approvals
CREATE TABLE IF NOT EXISTS approvals (
    id TEXT PRIMARY KEY,
    proposal_id TEXT NOT NULL,
    requested_by TEXT NOT NULL,
    decided_by TEXT,
    decision TEXT,
    decision_note TEXT,
    decided_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (requested_by) REFERENCES users(id),
    FOREIGN KEY (decided_by) REFERENCES users(id)
);

-- Audit trail
CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    details TEXT,
    result TEXT,
    timestamp TEXT NOT NULL,
    trace_id TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Changes and incidents
CREATE TABLE IF NOT EXISTS changes (
    id TEXT PRIMARY KEY,
    system_id TEXT NOT NULL,
    change_type TEXT NOT NULL,
    description TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    implemented_at TEXT,
    status TEXT NOT NULL,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS incidents (
    id TEXT PRIMARY KEY,
    system_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    severity TEXT NOT NULL,
    reported_by TEXT NOT NULL,
    reported_at TEXT NOT NULL,
    resolved_at TEXT,
    status TEXT NOT NULL,
    FOREIGN KEY (reported_by) REFERENCES users(id)
);

-- Access review
CREATE TABLE IF NOT EXISTS access_assignments (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    role TEXT NOT NULL,
    assigned_at TEXT NOT NULL,
    reviewed_at TEXT,
    status TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Evidence graph
CREATE TABLE IF NOT EXISTS graph_nodes (
    id TEXT PRIMARY KEY,
    node_type TEXT NOT NULL,
    label TEXT NOT NULL,
    attributes TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS graph_edges (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    edge_type TEXT NOT NULL,
    attributes TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (source_id) REFERENCES graph_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES graph_nodes(id) ON DELETE CASCADE
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_tokens_user_id ON tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_evidence_system_id ON evidence(system_id);
CREATE INDEX IF NOT EXISTS idx_assessments_system_id ON assessments(system_id);
CREATE INDEX IF NOT EXISTS idx_findings_assessment_id ON findings(assessment_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
"""


def init_database(db_path: str = "data/gxp.db") -> sqlite3.Connection:
    """Initialize database with schema if not exists.
    
    Returns a connection ready to use. Idempotent.
    """
    # Create directory if needed
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Connect
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    
    # Execute schema
    schema = get_schema_sql()
    conn.executescript(schema)
    conn.commit()
    
    # Seed default roles if they don't exist
    _seed_default_roles(conn)
    
    return conn


def _seed_default_roles(conn: sqlite3.Connection) -> None:
    """Seed default roles used in RBAC."""
    cursor = conn.execute("SELECT COUNT(*) FROM roles")
    if cursor.fetchone()[0] == 0:
        roles = [
            ("SYSTEM_OWNER", "System Owner - full access"),
            ("QA_REVIEWER", "QA Reviewer - audit and review"),
            ("AUDITOR", "Auditor - read-only audit access"),
            ("LEADERSHIP_VIEWER", "Leadership Viewer - dashboard only"),
            ("SECURITY_TESTER", "Security Tester - Assurance Lab access"),
        ]
        conn.executemany(
            "INSERT INTO roles (id, name, description) VALUES (?, ?, ?)",
            [(r[0], r[0], r[1]) for r in roles]
        )
        conn.commit()
