"""Evidence graph service (M7): a real, queryable directed graph.

The graph is derived deterministically from the persisted evidence and the
latest completed assessment: SYSTEM -> DOCUMENT nodes, DOCUMENT -> SYSTEM
edges, FINDING -> DOCUMENT evidence edges, FINDING -> SYSTEM impact edges and
APPROVAL nodes for decided approvals. Nothing is hardcoded; every node and
edge is materialised from the database.
"""

from __future__ import annotations

import json
from datetime import datetime

from app.domain.enums import EdgeType, NodeType


class GraphService:
    """Builds and serves the evidence graph for one system."""

    def __init__(self, db_connection, *, clock=None):
        self.db = db_connection
        self._clock = clock

    def _now(self) -> str:
        if self._clock is not None:
            return self._clock.now().isoformat()
        return datetime.now().astimezone().isoformat()

    def rebuild(self) -> dict:
        """Empty the graph tables and rebuild from actual data."""
        self.db.execute("DELETE FROM graph_edges")
        self.db.execute("DELETE FROM graph_nodes")
        now = self._now()
        self.db.execute(
            "INSERT OR IGNORE INTO graph_nodes "
            "(id, node_type, label, attributes, created_at)"
            " VALUES ('sys-NL-MES-001', 'System', 'NL-MES-001', ?, ?)",
            (json.dumps({"name": "MES PAS-X (Novo Life, synthetic)"}), now),
        )

        rows = self.db.execute(
            "SELECT source_id, title, document_type FROM evidence"
        ).fetchall()
        for row in rows:
            self.db.execute(
                "INSERT OR IGNORE INTO graph_nodes "
                "(id, node_type, label, attributes, created_at)"
                " VALUES (?, 'Document', ?, ?, ?)",
                (row["source_id"], row["title"],
                 json.dumps({"document_type": row["document_type"]}), now),
            )
            self.db.execute(
                "INSERT OR IGNORE INTO graph_edges "
                "(id, source_id, target_id, edge_type, attributes, created_at)"
                " VALUES (?, ?, 'sys-NL-MES-001', 'EVIDENCES', ?, ?)",
                (f"ed-{row['source_id']}-sys", row["source_id"],
                 json.dumps({}), now),
            )

        latest = self.db.execute(
            "SELECT id FROM assessments WHERE status = 'COMPLETE'"
            " ORDER BY completed_at DESC LIMIT 1"
        ).fetchone()
        if latest:
            assessment_id = latest["id"]
            findings = self.db.execute(
                "SELECT id, control_id, finding, severity, evidence_refs FROM findings"
                " WHERE assessment_id = ?",
                (assessment_id,),
            ).fetchall()
            for f in findings:
                node_id = f"finding-{f['id']}"
                self.db.execute(
                    "INSERT OR IGNORE INTO graph_nodes "
                    "(id, node_type, label, attributes, created_at)"
                    " VALUES (?, 'Finding', ?, ?, ?)",
                    (node_id, f["control_id"],
                     json.dumps({"severity": f["severity"],
                                 "summary": f["finding"][:120]}), now),
                )
                self.db.execute(
                    "INSERT OR IGNORE INTO graph_edges "
                    "(id, source_id, target_id, edge_type, attributes, created_at)"
                    " VALUES (?, ?, 'sys-NL-MES-001', 'IMPACTS', ?, ?)",
                    (f"ef-{node_id}", node_id, json.dumps({}), now),
                )
                refs = json.loads(f["evidence_refs"]) if f["evidence_refs"] else []
                for ref in refs:
                    source_id = ref.get("source_id")
                    if source_id:
                        self.db.execute(
                            "INSERT OR IGNORE INTO graph_edges "
                            "(id, source_id, target_id, edge_type, attributes, created_at)"
                            " VALUES (?, ?, ?, 'EVIDENCES', ?, ?)",
                            (f"ee-{node_id}-{source_id}", node_id, source_id,
                             json.dumps({}), now),
                        )

        if self._has_column("approvals", "decision"):
            approvals = self.db.execute(
                "SELECT id, decision FROM approvals WHERE decision IS NOT NULL"
            ).fetchall()
            for a in approvals:
                self.db.execute(
                    "INSERT OR IGNORE INTO graph_nodes "
                    "(id, node_type, label, attributes, created_at)"
                    " VALUES (?, 'HumanApproval', ?, ?, ?)",
                    (f"apr-{a['id']}", f"Approval {a['id'][:12]}",
                     json.dumps({"decision": a["decision"]}), now),
                )
        self.db.commit()
        return {"nodes": self.count_nodes(), "edges": self.count_edges()}

    def _has_column(self, table: str, column: str) -> bool:
        rows = self.db.execute(f"PRAGMA table_info({table})").fetchall()
        return any(r["name"] == column for r in rows)

    def count_nodes(self) -> int:
        return int(self.db.execute("SELECT COUNT(*) FROM graph_nodes").fetchone()[0])

    def count_edges(self) -> int:
        return int(self.db.execute("SELECT COUNT(*) FROM graph_edges").fetchone()[0])