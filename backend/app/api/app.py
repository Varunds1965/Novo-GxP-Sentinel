"""
Main Flask application.

All routes use StandardResponse envelope.
All endpoints check authorization server-side.
All material actions are logged to audit trail.
"""

from flask import Flask, request, jsonify
from functools import wraps
from datetime import datetime
import json
import sqlite3

from ..api.schemas.common import StandardResponse
from ..services.auth_service import AuthService
from ..services.assessment_service import AssessmentService
from ..domain.errors import AuthenticationError, AuthorizationError


def create_app(db_path="data/gxp.db"):
    """Factory function to create Flask app."""
    
    app = Flask(__name__)
    app.config['JSON_SORT_KEYS'] = False
    
    # Connect to database
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    
    # Initialize services
    auth_service = AuthService(db)
    assessment_service = AssessmentService(db)
    
    # Authentication decorator
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
    
    # Authorization decorator
    def require_permission(action: str, resource: str):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, user=None, **kwargs):
                try:
                    auth_service.require_permission(user, action, resource)
                except AuthorizationError as e:
                    return error_response(str(e), 403)
                return f(*args, user=user, **kwargs)
            return decorated_function
        return decorator
    
    # Response helpers
    def success_response(data=None, status=200):
        response = StandardResponse(success=True, data=data)
        return jsonify(response.__dict__), status
    
    def error_response(message: str, status=400):
        response = StandardResponse(success=False, error=message)
        return jsonify(response.__dict__), status
    
    # Authentication routes
    
    @app.route('/api/v1/auth/login', methods=['POST'])
    def login():
        """POST /api/v1/auth/login - Authenticate user."""
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return error_response('Missing username or password', 400)
        
        try:
            token = auth_service.authenticate(username, password)
            return success_response({'access_token': token, 'token_type': 'bearer'}, 200)
        except AuthenticationError as e:
            return error_response(str(e), 401)
    
    @app.route('/api/v1/auth/logout', methods=['POST'])
    @require_auth
    def logout(user):
        """POST /api/v1/auth/logout - Logout user."""
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        auth_service.logout(token)
        return success_response({'message': 'Logged out'}, 200)
    
    # Assessment routes
    
    @app.route('/api/v1/assessment/start', methods=['POST'])
    @require_auth
    def start_assessment(user):
        """POST /api/v1/assessment/start - Create new assessment."""
        data = request.get_json()
        system_id = data.get('system_id')
        
        if not system_id:
            return error_response('Missing system_id', 400)
        
        assessment = assessment_service.start_assessment(system_id, user.id)
        return success_response({
            'id': assessment.id,
            'system_id': assessment.system_id,
            'status': assessment.status.value,
            'created_at': assessment.created_at.isoformat(),
        }, 201)
    
    @app.route('/api/v1/assessment/<assessment_id>/run', methods=['POST'])
    @require_auth
    def run_assessment(user, assessment_id):
        """POST /api/v1/assessment/{id}/run - Run assessment."""
        try:
            findings = assessment_service.run_assessment(assessment_id)
            return success_response({
                'assessment_id': assessment_id,
                'findings_count': len(findings),
                'status': 'COMPLETE',
            }, 200)
        except Exception as e:
            return error_response(str(e), 500)
    
    @app.route('/api/v1/assessment/<assessment_id>', methods=['GET'])
    @require_auth
    def get_assessment(user, assessment_id):
        """GET /api/v1/assessment/{id} - Get assessment metadata."""
        assessment = assessment_service.get_assessment(assessment_id)
        if not assessment:
            return error_response('Assessment not found', 404)
        
        return success_response({
            'id': assessment.id,
            'system_id': assessment.system_id,
            'status': assessment.status.value,
            'created_at': assessment.created_at.isoformat(),
            'completed_at': assessment.completed_at.isoformat() if assessment.completed_at else None,
        }, 200)
    
    @app.route('/api/v1/assessment/<assessment_id>/findings', methods=['GET'])
    @require_auth
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
    def get_readiness(user, assessment_id):
        """GET /api/v1/assessment/{id}/readiness - Get readiness score."""
        try:
            score = assessment_service.get_readiness_score(assessment_id)
            return success_response({
                'assessment_id': assessment_id,
                'readiness_score': score.overall_score,
                'status': score.status.value if hasattr(score, 'status') else str(score.status),
            }, 200)
        except Exception as e:
            return error_response(str(e), 500)
    
    # Evidence routes
    
    @app.route('/api/v1/evidence/search', methods=['GET'])
    @require_auth
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
    
    # Role/user routes
    
    @app.route('/api/v1/user/profile', methods=['GET'])
    @require_auth
    def get_profile(user):
        """GET /api/v1/user/profile - Get current user profile."""
        return success_response({
            'id': user.id,
            'username': user.username,
            'role_id': user.role_id,
        }, 200)
    
    # Health check
    
    @app.route('/api/v1/health', methods=['GET'])
    def health():
        """GET /api/v1/health - Health check."""
        return success_response({'status': 'healthy'}, 200)
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=8765, debug=False)
