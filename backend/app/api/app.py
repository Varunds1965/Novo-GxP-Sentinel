"""
Main Flask application.

All routes use StandardResponse envelope.
All endpoints check authorization server-side.
All material actions are logged to audit trail.
"""

import json
import os
import sys
import uuid
from pathlib import Path

from flask import Flask, request, jsonify, g
from functools import wraps
from datetime import datetime

# Add backend to path for proper imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.api.schemas.common import StandardResponse
from app.services.auth_service import AuthService
from app.services.assessment_service import AssessmentService
from app.services.evidence_service import EvidenceService
from app.services.copilot_service import CopilotService
from app.services.graph_service import GraphService
from app.services.report_service import ReportService
from app.services.assurance_lab_service import AssuranceLabService
from app.actions.action_gateway import ActionGateway
from app.domain.errors import (
    AuthenticationError,
    AuthorizationError,
    GxpSentinelError,
)
from app.domain.enums import Severity
from app.database import init_database
from app.audit.chain import AuditChain

# Repository root: backend/app/api/app.py -> parents[3] is the checkout root.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_CORPUS_DIR = _REPO_ROOT / "data" / "corpus"
_DEFAULT_CHECKLISTS = _REPO_ROOT / "data" / "demo" / "audit_checklists.json"


def create_app(db_path="data/gxp.db"):
    """Factory function to create Flask app."""
    
    app = Flask(__name__)
    app.config['JSON_SORT_KEYS'] = False
    
    # Initialize database
    db = init_database(db_path)
    
    # Data locations are configurable so tests and deployments can repoint them
    # without code edits; defaults resolve inside the repository checkout.
    corpus_dir = os.environ.get("GXP_CORPUS_DIR", str(_DEFAULT_CORPUS_DIR))
    checklists_path = os.environ.get(
        "GXP_CHECKLISTS_PATH", str(_DEFAULT_CHECKLISTS)
    )
    
    # Initialize services
    auth_service = AuthService(db)
    assessment_service = AssessmentService(
        db, corpus_dir=corpus_dir, checklists_path=checklists_path
    )
    evidence_service = EvidenceService(db)
    copilot_service = CopilotService(db, assessment_service)
    graph_service = GraphService(db)
    report_service = ReportService(db)
    assurance_lab = AssuranceLabService(
        db,
        copilot_service=copilot_service,
        evidence_service=evidence_service,
        auth_service=auth_service,
    )
    action_gateway = ActionGateway(db)
    audit_chain = AuditChain(db)
    # Exposed so tests and the WSGI server can close the connection cleanly
    # (matters on Windows, where an open handle blocks temp-dir deletion).
    app.config['DB_CONNECTION'] = db
    
    # ---- Per-request database connection management ----
    
    @app.before_request
    def before_request():
        """Store db connection in request context."""
        g.db = db
        g.auth_service = auth_service
        g.assessment_service = assessment_service
        g.audit_chain = audit_chain
        g.evidence_service = evidence_service
        g.copilot_service = copilot_service
        g.graph_service = graph_service
        g.report_service = report_service
        g.assurance_lab = assurance_lab
        g.action_gateway = action_gateway
    
    # ---- Authentication decorator ----
    
    def require_auth(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if not token:
                return error_response('Missing authentication token', 401)
            
            try:
                user = auth_service.verify_token(token)
            except AuthenticationError as e:
                return error_response(str(e), 401)
            
            return f(user=user, *args, **kwargs)
        return decorated_function
    
    # ---- Authorization decorator (NOW ACTUALLY APPLIED) ----
    
    def require_permission(action: str, resource: str):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, user=None, **kwargs):
                try:
                    auth_service.require_permission(user, action, resource)
                except AuthorizationError as e:
                    # Log authorization failure
                    try:
                        audit_chain.log_action(
                            user_id=user.id if user else None,
                            action="AUTHORIZATION_DENIED",
                            resource_type=resource,
                            resource_id="",
                            details=f"Action {action} denied",
                            result="DENIED",
                            trace_id=request.headers.get('X-Trace-ID', '')
                        )
                    except Exception:
                        pass  # Continue even if audit fails
                    return error_response(str(e), 403)
                return f(*args, user=user, **kwargs)
            return decorated_function
        return decorator
    
    # ---- Response helpers ----
    
    def success_response(data=None, status=200):
        response = StandardResponse(success=True, data=data)
        return jsonify(response.__dict__), status
    
    def error_response(message: str, status=400):
        response = StandardResponse(success=False, error=message)
        return jsonify(response.__dict__), status
    
    def log_action(user_id, action, resource_type, resource_id, details=None, result="SUCCESS"):
        """Log action to audit trail."""
        try:
            audit_chain.log_action(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details or "",
                result=result,
                trace_id=request.headers.get('X-Trace-ID', '')
            )
        except Exception as e:
            app.logger.warning(f"Audit logging failed: {e}")
    
    # ---- Authentication routes ----
    
    @app.route('/api/v1/auth/login', methods=['POST'])
    def login():
        """POST /api/v1/auth/login - Authenticate user."""
        data = request.get_json() or {}
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return error_response('Missing username or password', 400)
        
        try:
            token = auth_service.authenticate(username, password)
            log_action(username, "LOGIN", "AUTH", username, result="SUCCESS")
            return success_response({
                'access_token': token,
                'token_type': 'bearer',
                'expires_in': 3600
            }, 200)
        except AuthenticationError as e:
            log_action(username, "LOGIN", "AUTH", username, result="FAILED")
            return error_response(str(e), 401)
    
    @app.route('/api/v1/auth/logout', methods=['POST'])
    @require_auth
    def logout(user):
        """POST /api/v1/auth/logout - Logout user."""
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        auth_service.logout(token)
        log_action(user.id, "LOGOUT", "AUTH", user.id, result="SUCCESS")
        return success_response({'message': 'Logged out'}, 200)
    
    # ---- Assessment routes (NOW WITH AUTHORIZATION) ----
    
    @app.route('/api/v1/assessment/start', methods=['POST'])
    @require_auth
    @require_permission('PROPOSE', 'ASSESSMENT')
    def start_assessment(user):
        """POST /api/v1/assessment/start - Create new assessment."""
        data = request.get_json() or {}
        system_id = data.get('system_id')
        
        if not system_id:
            return error_response('Missing system_id', 400)
        
        assessment = assessment_service.start_assessment(system_id, user.id)
        log_action(user.id, "START_ASSESSMENT", "ASSESSMENT", assessment.id, result="SUCCESS")
        return success_response({
            'id': assessment.id,
            'system_id': assessment.system_id,
            'status': assessment.status,
            'created_at': assessment.created_at.isoformat() if hasattr(assessment.created_at, 'isoformat') else str(assessment.created_at),
        }, 201)
    
    @app.route('/api/v1/assessment/<assessment_id>/run', methods=['POST'])
    @require_auth
    @require_permission('PROPOSE', 'ASSESSMENT')
    def run_assessment(user, assessment_id):
        """POST /api/v1/assessment/{id}/run - Run assessment."""
        try:
            findings = assessment_service.run_assessment(assessment_id)
            log_action(user.id, "RUN_ASSESSMENT", "ASSESSMENT", assessment_id, result="SUCCESS")
            return success_response({
                'assessment_id': assessment_id,
                'findings_count': len(findings),
                'status': 'COMPLETE',
            }, 200)
        except Exception as e:
            log_action(user.id, "RUN_ASSESSMENT", "ASSESSMENT", assessment_id, result="FAILED")
            return error_response(str(e), 500)
    
    @app.route('/api/v1/assessment/<assessment_id>', methods=['GET'])
    @require_auth
    @require_permission('READ', 'ASSESSMENT')
    def get_assessment(user, assessment_id):
        """GET /api/v1/assessment/{id} - Get assessment metadata."""
        assessment = assessment_service.get_assessment(assessment_id)
        if not assessment:
            return error_response('Assessment not found', 404)
        
        return success_response({
            'id': assessment.id,
            'system_id': assessment.system_id,
            'status': assessment.status,
            'created_at': assessment.created_at.isoformat() if hasattr(assessment.created_at, 'isoformat') else str(assessment.created_at),
            'completed_at': assessment.completed_at.isoformat() if assessment.completed_at and hasattr(assessment.completed_at, 'isoformat') else None,
        }, 200)
    
    @app.route('/api/v1/assessment/<assessment_id>/findings', methods=['GET'])
    @require_auth
    @require_permission('READ', 'ASSESSMENT')
    def get_findings(user, assessment_id):
        """GET /api/v1/assessment/{id}/findings - Get findings.

        Optional ?severity=HIGH filters to one named severity. Severity is an
        ordered IntEnum internally; the API exposes both the deterministic
        ordinal (severity_level) and its named level (severity).
        """
        severity_filter = (request.args.get('severity') or '').upper()
        valid_severities = {s.name for s in Severity}
        if severity_filter and severity_filter not in valid_severities:
            return error_response(
                f"Unknown severity '{severity_filter}'. "
                f"Valid: {', '.join(sorted(valid_severities))}", 400,
            )
        findings = assessment_service.get_findings(assessment_id)
        
        serialized = [
            {
                'id': f.id,
                'control_id': f.control_id,
                'finding': f.finding,
                'severity': f.severity.name if hasattr(f.severity, 'name') else str(f.severity),
                'severity_level': int(f.severity),
                'confidence': f.confidence.value if hasattr(f.confidence, 'value') else str(f.confidence),
                'evidence_refs': f.evidence_refs,
            }
            for f in findings
        ]
        if severity_filter:
            serialized = [x for x in serialized if x['severity'] == severity_filter]
        
        data = {
            'assessment_id': assessment_id,
            'findings': serialized,
            'total': len(serialized),
        }
        
        return success_response(data, 200)
    
    @app.route('/api/v1/assessment/<assessment_id>/readiness', methods=['GET'])
    @require_auth
    @require_permission('READ', 'ASSESSMENT')
    def get_readiness(user, assessment_id):
        """GET /api/v1/assessment/{id}/readiness - Get readiness score."""
        try:
            score = assessment_service.get_readiness_score(assessment_id)
            return success_response({
                'assessment_id': assessment_id,
                'readiness_score': score.overall_score,
                'status': score.status.value if hasattr(score.status, 'value') else str(score.status),
            }, 200)
        except Exception as e:
            return error_response(str(e), 500)
    
    # ---- Evidence routes ----
    
    @app.route('/api/v1/evidence/search', methods=['GET'])
    @require_auth
    @require_permission('READ', 'EVIDENCE')
    def search_evidence(user):
        """GET /api/v1/evidence/search - Search evidence."""
        query = request.args.get('q', '')
        if not query:
            return error_response('Missing query', 400)
        
        results = assessment_service.search_evidence(query)
        return success_response({
            'query': query,
            'results': results,
            'count': len(results),
        }, 200)
    
    @app.route('/api/v1/evidence/upload', methods=['POST'])
    @require_auth
    @require_permission('INGEST', 'EVIDENCE')
    def upload_evidence(user):
        """POST /api/v1/evidence/upload - Upload evidence.

        Multipart form: `file` (required) and `system_id` (required). The file
        goes through the full twelve-step ingestion pipeline: nothing is TRUSTED
        on arrival, quarantined content is never indexed (SEC-R-015/016).
        """
        if 'file' not in request.files:
            return error_response("Missing file part named 'file'", 400)
        uploaded = request.files['file']
        system_id = request.form.get('system_id', '')
        if not system_id:
            return error_response('Missing system_id', 400)
        document_type = request.form.get('document_type', 'UPLOADED_EVIDENCE')
        payload = uploaded.read()

        try:
            result = evidence_service.ingest(
                filename=uploaded.filename or '',
                payload=payload,
                uploaded_by=user.id,
                system_id=system_id,
                document_type=document_type,
            )
        except GxpSentinelError as e:
            # Domain errors carry their own HTTP status (413/415/422/400...).
            log_action(
                user.id, "UPLOAD_EVIDENCE", "EVIDENCE",
                uploaded.filename or "", details=e.code, result="REJECTED",
            )
            return error_response(e.human_message, e.http_status)

        log_action(
            user.id, "UPLOAD_EVIDENCE", "EVIDENCE", result['source_id'],
            details=(
                f"trust={result['trust_level']} quarantined={result['quarantined']} "
                f"chunks={result['chunks_indexed']}"
            ),
            result="QUARANTINED" if result['quarantined'] else "SUCCESS",
        )
        return success_response(result, 201)
    
    # ---- User/profile routes ----
    
    @app.route('/api/v1/user/profile', methods=['GET'])
    @require_auth
    def get_profile(user):
        """GET /api/v1/user/profile - Get current user profile."""
        return success_response({
            'id': user.id,
            'username': user.username,
            'role_id': user.role_id,
        }, 200)
    
    # ---- Copilot / RAG routes (M5: deterministic, grounded, zero-cloud) ----
    
    @app.route('/api/v1/copilot/ask', methods=['POST'])
    @require_auth
    @require_permission('READ', 'COPILOT')
    def copilot_ask(user):
        """POST /api/v1/copilot/ask - Ask GxP Copilot.

        Answers are composed only from retrieved, provenance-scored local
        evidence. When no evidence clears the relevance floor the copilot
        refuses with INSUFFICIENT_EVIDENCE rather than inventing an answer.
        """
        data = request.get_json() or {}
        question = (data.get('question') or '').strip()
        if not question:
            return error_response('Missing question', 400)

        result = copilot_service.ask(question, user_id=user.id)
        log_action(
            user.id, "COPILOT_ASK", "COPILOT", "",
            details=f"grounded={result['grounded']} q={question[:120]}",
            result="SUCCESS",
        )
        return success_response(result, 200)
    
    # ---- Graph routes (M7: derived from persisted evidence + findings) ----
    
    @app.route('/api/v1/graph/nodes', methods=['GET'])
    @require_auth
    @require_permission('READ', 'GRAPH')
    def get_graph_nodes(user):
        """GET /api/v1/graph/nodes - Get evidence graph nodes and edges.

        Returns the materialised graph. Pass ?rebuild=true to re-derive it
        from the current evidence, findings and approvals first.
        """
        if request.args.get('rebuild', '').lower() in {'1', 'true', 'yes'}:
            counts = graph_service.rebuild()
            log_action(
                user.id, "GRAPH_REBUILD", "GRAPH", "",
                details=f"nodes={counts['nodes']} edges={counts['edges']}",
            )
        nodes = [
            {
                'id': row['id'],
                'node_type': row['node_type'],
                'label': row['label'],
                'attributes': json.loads(row['attributes']) if row['attributes'] else {},
            }
            for row in db.execute(
                "SELECT id, node_type, label, attributes FROM graph_nodes"
                " ORDER BY node_type, id"
            ).fetchall()
        ]
        edges = [
            {
                'id': row['id'],
                'source_id': row['source_id'],
                'target_id': row['target_id'],
                'edge_type': row['edge_type'],
                'attributes': json.loads(row['attributes']) if row['attributes'] else {},
            }
            for row in db.execute(
                "SELECT id, source_id, target_id, edge_type, attributes"
                " FROM graph_edges ORDER BY edge_type, id"
            ).fetchall()
        ]
        return success_response({'nodes': nodes, 'edges': edges}, 200)
    
    # ---- Approval routes (M8: human approval workflow) ----
    
    @app.route('/api/v1/approvals', methods=['GET'])
    @require_auth
    @require_permission('READ', 'APPROVALS')
    def list_approvals(user):
        """GET /api/v1/approvals - List approvals, newest first.

        Optional ?status=PENDING returns only undecided requests.
        """
        status_filter = request.args.get('status')
        rows = db.execute(
            "SELECT * FROM approvals ORDER BY created_at DESC"
        ).fetchall()
        approvals = []
        for row in rows:
            decided = row['decision'] is not None
            if status_filter == 'PENDING' and decided:
                continue
            approvals.append({
                'id': row['id'],
                'proposal_id': row['proposal_id'],
                'requested_by': row['requested_by'],
                'decided_by': row['decided_by'],
                'decision': row['decision'],
                'decision_note': row['decision_note'],
                'decided_at': row['decided_at'],
                'created_at': row['created_at'],
                'status': 'DECIDED' if decided else 'PENDING',
            })
        return success_response({'approvals': approvals, 'total': len(approvals)}, 200)
    
    @app.route('/api/v1/approvals', methods=['POST'])
    @require_auth
    @require_permission('PROPOSE', 'ASSESSMENT')
    def create_approval(user):
        """POST /api/v1/approvals - Request human approval for a proposal."""
        data = request.get_json() or {}
        proposal_id = data.get('proposal_id')
        if not proposal_id:
            return error_response('Missing proposal_id', 400)
        assessment = assessment_service.get_assessment(proposal_id)
        if assessment is None:
            return error_response(
                'proposal_id does not reference a known assessment', 404)
        
        approval_id = f"appr-{uuid.uuid4().hex[:12]}"
        now = datetime.now().astimezone().isoformat()
        db.execute(
            "INSERT INTO approvals (id, proposal_id, requested_by, created_at)"
            " VALUES (?, ?, ?, ?)",
            (approval_id, proposal_id, user.id, now),
        )
        db.commit()
        log_action(
            user.id, "REQUEST_APPROVAL", "APPROVALS", approval_id,
            details=f"proposal={proposal_id}",
        )
        return success_response({
            'id': approval_id,
            'proposal_id': proposal_id,
            'requested_by': user.id,
            'status': 'PENDING',
            'created_at': now,
        }, 201)
    
    @app.route('/api/v1/approvals/<approval_id>/decide', methods=['POST'])
    @require_auth
    @require_permission('APPROVE', 'APPROVALS')
    def decide_approval(user, approval_id):
        """POST /api/v1/approvals/{id}/decide - Make approval decision.

        Body: {"decision": "APPROVED" | "REJECTED", "note": "..."}. A decision
        is final: an already-decided approval cannot be re-decided (409) and a
        requester can never decide their own request (403). Decisions are
        taken by a named human and recorded in the audit trail; no model
        output ever appears in an approval dialog.
        """
        data = request.get_json() or {}
        decision = data.get('decision')
        note = data.get('note', '')
        
        if decision not in {'APPROVED', 'REJECTED'}:
            return error_response(
                "decision must be 'APPROVED' or 'REJECTED'", 400)
        
        row = db.execute(
            "SELECT * FROM approvals WHERE id = ?", (approval_id,)
        ).fetchone()
        if row is None:
            return error_response('Approval not found', 404)
        if row['decision'] is not None:
            return error_response(
                f"Approval already decided ({row['decision']}) by "
                f"{row['decided_by']}", 409,
            )
        if row['requested_by'] == user.id:
            return error_response(
                'Self-approval is not permitted: the requester cannot decide '
                'their own approval request.', 403,
            )
        
        now = datetime.now().astimezone().isoformat()
        db.execute(
            "UPDATE approvals SET decided_by = ?, decision = ?, decision_note = ?,"
            " decided_at = ? WHERE id = ?",
            (user.id, decision, note, now, approval_id),
        )
        db.commit()
        
        # The decision is executed through the Action Gateway, which is a
        # log-only mock in this prototype: nothing touches a real system.
        action_result = action_gateway.execute_approved_action(
            action_id=approval_id,
            user_id=user.id,
            action_type='APPROVE_ASSESSMENT_RESULTS',
            params={'proposal_id': row['proposal_id'], 'decision': decision},
        )
        log_action(
            user.id, "DECIDE_APPROVAL", "APPROVALS", approval_id,
            details=(
                f"decision={decision} proposal={row['proposal_id']} "
                f"note={note[:200]}"
            ),
            result=decision,
        )
        return success_response({
            'id': approval_id,
            'proposal_id': row['proposal_id'],
            'decision': decision,
            'decided_by': user.id,
            'decided_at': now,
            'note': note,
            'action_result': {
                'success': action_result.success,
                'message': action_result.message,
            },
        }, 200)
    
    # ---- Assurance Lab routes (M8: deterministic adversarial probes) ----
    
    @app.route('/api/v1/assurance-lab/scenario/<scenario_id>/run', methods=['POST'])
    @require_auth
    @require_permission('RUN_ASSURANCE_LAB', 'ASSURANCE_LAB')
    def run_scenario(user, scenario_id):
        """POST /api/v1/assurance-lab/scenario/{id}/run - Run lab scenario.

        Every scenario is a deterministic probe against a real component
        (injection scanner, ingestion pipeline, retrieval, RBAC, readiness).
        Results are computed live from the running system, never canned.
        """
        try:
            result = assurance_lab.run_scenario(scenario_id, user=user)
        except KeyError:
            return error_response(
                f"Unknown scenario '{scenario_id}'. Known scenarios: "
                f"{', '.join(sorted(assurance_lab.scenario_ids()))}", 404,
            )
        except GxpSentinelError as e:
            return error_response(e.human_message, e.http_status)
        log_action(
            user.id, "RUN_ASSURANCE_LAB", "ASSURANCE_LAB", scenario_id,
            details=f"passed={result['passed']}", result="SUCCESS",
        )
        return success_response(result, 200)
    
    # ---- Report / evidence pack (M9) ----
    
    @app.route('/api/v1/assessment/<assessment_id>/report', methods=['GET'])
    @require_auth
    @require_permission('EXPORT', 'REPORTS')
    def export_report(user, assessment_id):
        """GET /api/v1/assessment/{id}/report - Export the evidence pack.

        The pack assembles the assessment, its findings, the readiness
        snapshot, evidence provenance, approvals and the audit events for this
        assessment, with a SHA-256 digest over the canonical content.
        """
        try:
            pack = report_service.build_evidence_pack(assessment_id, requested_by=user.id)
        except GxpSentinelError as e:
            return error_response(e.human_message, e.http_status)
        log_action(
            user.id, "EXPORT_REPORT", "REPORTS", assessment_id,
            details=f"pack_id={pack['pack_id']} sha256={pack['sha256'][:16]}...",
        )
        return success_response(pack, 200)
    
    # ---- Health check (PUBLIC, no auth required) ----
    
    @app.route('/api/v1/health', methods=['GET'])
    def health():
        """GET /api/v1/health - Health check."""
        return success_response({
            'status': 'healthy',
            'database': 'connected',
            'version': '1.0.0'
        }, 200)
    
    # ---- Error handlers ----
    
    @app.errorhandler(404)
    def not_found(error):
        return error_response('Not found', 404)
    
    @app.errorhandler(500)
    def internal_error(error):
        # An unhandled exception must never be invisible to the operator:
        # write the full traceback to a server-side file (and stderr) and
        # return only a safe message to the client.
        import traceback as _tb
        detail = _tb.format_exc()
        try:
            with open("data/server_errors.log", "a", encoding="utf-8") as fh:
                fh.write(f"[{datetime.now().astimezone().isoformat()}] "
                         f"{request.method} {request.path}\n{detail}\n")
        except OSError:
            pass
        app.logger.exception(
            "Unhandled exception on %s %s", request.method, request.path
        )
        return error_response('Internal server error', 500)
    
    return app


if __name__ == '__main__':
    app = create_app()
    print("Starting GxP Sentinel API on 127.0.0.1:8765...")
    app.run(host='127.0.0.1', port=8765, debug=False, threaded=False)
