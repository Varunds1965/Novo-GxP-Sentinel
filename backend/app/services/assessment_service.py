"""Assessment service orchestrates the deterministic core."""

import json
from datetime import datetime
from typing import List, Optional

from ..domain.models import Assessment, Finding, ReadinessScore
from ..domain.enums import AssessmentStatus
from ..rules.checklist_engine import ChecklistEngine
from ..rules.readiness import ReadinessCalculator
from ..rag.retrieval import EvidenceRetriever


class AssessmentService:
    """Manages assessment lifecycle and orchestrates the deterministic engine."""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.engine = ChecklistEngine(db_connection)
        self.readiness = ReadinessCalculator()
        self.retriever = EvidenceRetriever(db_connection)
    
    def start_assessment(self, system_id: str, user_id: str) -> Assessment:
        """Create a new assessment."""
        assessment = Assessment(
            id=f"assess_{datetime.utcnow().isoformat().replace(':', '-')}",
            system_id=system_id,
            user_id=user_id,
            status=AssessmentStatus.PENDING,
            created_at=datetime.utcnow(),
        )
        
        # Store in database
        self.db.execute(
            """
            INSERT INTO assessments (id, system_id, user_id, status, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (assessment.id, system_id, user_id, assessment.status.value, 
             assessment.created_at.isoformat())
        )
        self.db.commit()
        
        return assessment
    
    def run_assessment(self, assessment_id: str) -> List[Finding]:
        """
        Execute the 350-control assessment.
        
        This calls the deterministic checklist engine, which owns all findings,
        severities, and confidence levels. The LLM (if available) explains only.
        """
        # Update status
        self.db.execute(
            "UPDATE assessments SET status = ? WHERE id = ?",
            (AssessmentStatus.RUNNING.value, assessment_id)
        )
        self.db.commit()
        
        try:
            # Run deterministic engine (this is the core)
            findings = self.engine.evaluate_all_controls()
            
            # Store findings
            for finding in findings:
                self._store_finding(assessment_id, finding)
            
            # Update status
            self.db.execute(
                "UPDATE assessments SET status = ?, completed_at = ? WHERE id = ?",
                (AssessmentStatus.COMPLETE.value, datetime.utcnow().isoformat(), 
                 assessment_id)
            )
            self.db.commit()
            
            return findings
        
        except Exception as e:
            self.db.execute(
                "UPDATE assessments SET status = ? WHERE id = ?",
                (AssessmentStatus.FAILED.value, assessment_id)
            )
            self.db.commit()
            raise
    
    def get_assessment(self, assessment_id: str) -> Optional[Assessment]:
        """Fetch assessment metadata."""
        cursor = self.db.execute(
            """
            SELECT id, system_id, user_id, status, created_at, completed_at
            FROM assessments WHERE id = ?
            """,
            (assessment_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        
        return Assessment(
            id=row[0],
            system_id=row[1],
            user_id=row[2],
            status=AssessmentStatus(row[3]),
            created_at=datetime.fromisoformat(row[4]),
            completed_at=datetime.fromisoformat(row[5]) if row[5] else None,
        )
    
    def get_findings(self, assessment_id: str) -> List[Finding]:
        """Fetch all findings for an assessment."""
        cursor = self.db.execute(
            """
            SELECT id, assessment_id, control_id, finding, severity, confidence, 
                   evidence_refs, created_at
            FROM findings WHERE assessment_id = ?
            """,
            (assessment_id,)
        )
        
        findings = []
        for row in cursor.fetchall():
            evidence_refs = json.loads(row[6]) if row[6] else []
            findings.append(Finding(
                id=row[0],
                assessment_id=row[1],
                control_id=row[2],
                finding=row[3],
                severity=row[4],
                confidence=row[5],
                evidence_refs=evidence_refs,
                created_at=datetime.fromisoformat(row[7]),
            ))
        
        return findings
    
    def get_readiness_score(self, assessment_id: str) -> ReadinessScore:
        """Calculate system readiness based on findings."""
        findings = self.get_findings(assessment_id)
        score = self.readiness.calculate(findings)
        return score
    
    def search_evidence(self, query: str, assessment_id: Optional[str] = None) -> List:
        """Search evidence using FTS5."""
        results = self.retriever.search(query)
        return results
    
    # Private methods
    
    def _store_finding(self, assessment_id: str, finding: Finding) -> None:
        """Store finding in database."""
        self.db.execute(
            """
            INSERT INTO findings 
            (id, assessment_id, control_id, finding, severity, confidence, 
             evidence_refs, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (finding.id, assessment_id, finding.control_id, finding.finding,
             finding.severity.value, finding.confidence.value,
             json.dumps(finding.evidence_refs),
             finding.created_at.isoformat())
        )
        self.db.commit()
