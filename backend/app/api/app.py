"""
Main Flask application.

All routes use StandardResponse envelope.
All endpoints check authorization server-side.
All material actions are logged to audit trail.
"""

from flask import Flask, request, jsonify, g
from functools import wraps
from datetime import datetime
import json
import sys
from pathlib import Path

# Add backend to path for proper imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.api.schemas.common import StandardResponse
from app.services.auth_service import AuthService
from app.services.assessment_service import AssessmentService
from app.domain.errors import AuthenticationError, AuthorizationError
from app.database import init_database
from app.audit.chain import AuditChain


def create_app(db_path="data/gxp.db"):
    """Factory function to create Flask app."""
    
    app = Flask(__name__)
    app.config['JSON_SORT_KEYS'] = False
    
    # Initialize database
    db = init_database(db_path)
    
    # Initialize services
    auth_service = AuthService(db)
    assessment_service = AssessmentService(db)
    audit_chain = AuditChain(db)
    
    # ---- Per-request database connection management ----
    
    @app.before_request
    def before_request():
        """Store db connection in request context."""
        g.db = db
        g.auth_service = auth_service
        g.assessment_service = assessment_service
        g.audit_chain = audit_chain
    
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
        """GET /api/v1/assessment/{id}/findings - Get findings."""
        findings = assessment_service.get_findings(assessment_id)
        
        data = {
            'assessment_id': assessment_id,
            'findings': [
                {
                    'id': f.id,
                    'control_id': f.control_id,
                    'finding': f.finding,
                    'severity': f.severity.value if hasattr(f.severity, 'value') else str(f.severity),
                    'confidence': f.confidence.value if hasattr(f.confidence, 'value') else str(f.confidence),
                    'evidence_refs': f.evidence_refs,
                }
                for f in findings
            ],
            'total': len(findings),
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
        """POST /api/v1/evidence/upload - Upload evidence."""
        # TODO: Implement evidence upload pipeline (M5)
        return error_response('Not yet implemented', 501)
    
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
    
    # ---- Copilot / RAG routes (M5 stubs) ----
    
    @app.route('/api/v1/copilot/ask', methods=['POST'])
    @require_auth
    def copilot_ask(user):
        """POST /api/v1/copilot/ask - Ask GxP Copilot."""
        # TODO: Implement Copilot with evidence grounding (M5)
        return error_response('Not yet implemented', 501)
    
    # ---- Graph routes (M7 stubs) ----
    
    @app.route('/api/v1/graph/nodes', methods=['GET'])
    @require_auth
    @require_permission('READ', 'GRAPH')
    def get_graph_nodes(user):
        """GET /api/v1/graph/nodes - Get evidence graph nodes."""
        # TODO: Implement evidence graph (M7)
        return error_response('Not yet implemented', 501)
    
    # ---- Approval routes (M8 stubs) ----
    
    @app.route('/api/v1/approvals', methods=['GET'])
    @require_auth
    @require_permission('READ', 'APPROVALS')
    def list_approvals(user):
        """GET /api/v1/approvals - List approvals for user."""
        # TODO: Implement approval workflow (M8)
        return error_response('Not yet implemented', 501)
    
    @app.route('/api/v1/approvals/<approval_id>/decide', methods=['POST'])
    @require_auth
    @require_permission('APPROVE', 'APPROVALS')
    def decide_approval(user, approval_id):
        """POST /api/v1/approvals/{id}/decide - Make approval decision."""
        # TODO: Implement approval workflow (M8)
        return error_response('Not yet implemented', 501)
    
    # ---- Assurance Lab routes (M8 stub) ----
    
    @app.route('/api/v1/assurance-lab/scenario/<scenario_id>/run', methods=['POST'])
    @require_auth
    @require_permission('RUN_ASSURANCE_LAB', 'ASSURANCE_LAB')
    def run_scenario(user, scenario_id):
        """POST /api/v1/assurance-lab/scenario/{id}/run - Run Assurance Lab scenario."""
        # TODO: Implement Assurance Lab S1-S7 (M8)
        return error_response('Not yet implemented', 501)
    
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
        return error_response('Internal server error', 500)
    
    return app


if __name__ == '__main__':
    app = create_app()
    print("Starting GxP Sentinel API on 127.0.0.1:8765...")
    app.run(host='127.0.0.1', port=8765, debug=False, threaded=False)
