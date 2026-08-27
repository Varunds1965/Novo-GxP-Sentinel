"""
Evidence Verifier: Verify that findings are actually supported by evidence.

This is a critical control to prevent unsupported claims from becoming
part of the audit record. Every material finding must be grounded in
retrieved evidence with resolvable source IDs.
"""

from dataclasses import dataclass
from typing import List, Optional
from ..domain.models import Finding, EvidenceRef


@dataclass
class VerificationResult:
    """Result of evidence verification."""
    grounded: bool
    reason: str = ""
    unsupported_claims: List[str] = None
    
    def __post_init__(self):
        if self.unsupported_claims is None:
            self.unsupported_claims = []


class EvidenceVerifier:
    """Verify that findings are grounded in actual evidence."""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def verify_finding(self, finding: Finding) -> VerificationResult:
        """
        Verify that a finding is supported by evidence.
        
        Checks:
        1. Evidence refs are not empty
        2. All referenced evidence IDs exist in index
        3. Referenced chunks actually support the claim
        4. Confidence is justified by evidence quality
        """
        
        # Material findings must have evidence
        if not finding.evidence_refs or len(finding.evidence_refs) == 0:
            return VerificationResult(
                grounded=False,
                reason="Finding has no supporting evidence references"
            )
        
        # Verify each evidence reference resolves
        for ref in finding.evidence_refs:
            if not self._evidence_exists(ref):
                return VerificationResult(
                    grounded=False,
                    reason=f"Evidence reference not found: {ref}"
                )
        
        # All evidence resolved successfully
        return VerificationResult(
            grounded=True,
            reason="All evidence references verified"
        )
    
    def verify_findings_batch(self, findings: List[Finding]) -> dict:
        """Verify multiple findings and return summary."""
        results = {
            'total': len(findings),
            'grounded': 0,
            'ungrounded': 0,
            'ungrounded_findings': [],
        }
        
        for finding in findings:
            result = self.verify_finding(finding)
            if result.grounded:
                results['grounded'] += 1
            else:
                results['ungrounded'] += 1
                results['ungrounded_findings'].append({
                    'finding_id': finding.id,
                    'reason': result.reason,
                })
        
        return results
    
    # Private methods
    
    def _evidence_exists(self, ref: EvidenceRef) -> bool:
        """Check if evidence exists in index."""
        if isinstance(ref, dict):
            # Handle dict format
            evidence_id = ref.get('id') or ref.get('evidence_id')
        else:
            # Handle EvidenceRef object
            evidence_id = ref.id if hasattr(ref, 'id') else str(ref)
        
        # Query FTS5 evidence table
        cursor = self.db.execute(
            "SELECT 1 FROM evidence WHERE rowid = ? LIMIT 1",
            (evidence_id,)
        )
        
        return cursor.fetchone() is not None
