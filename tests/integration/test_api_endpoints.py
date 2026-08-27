"""Integration tests for M3 API endpoints."""

import unittest
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.api.app import create_app


class TestAPIEndpoints(unittest.TestCase):
    """Test API endpoints for M3."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app(":memory:")  # In-memory SQLite
        self.client = self.app.test_client()
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get('/api/v1/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
    
    def test_login_missing_credentials(self):
        """Test login with missing credentials."""
        response = self.client.post('/api/v1/auth/login', json={})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
    
    def test_assessment_requires_auth(self):
        """Test that assessment routes require authentication."""
        response = self.client.post('/api/v1/assessment/start', json={
            'system_id': 'pas-x'
        })
        self.assertEqual(response.status_code, 401)
    
    def test_evidence_search_requires_auth(self):
        """Test that evidence search requires authentication."""
        response = self.client.get('/api/v1/evidence/search?q=test')
        self.assertEqual(response.status_code, 401)
    
    def test_response_includes_trace_id(self):
        """Test that all responses include trace_id."""
        response = self.client.get('/api/v1/health')
        data = json.loads(response.data)
        self.assertIn('trace_id', data)
        self.assertIsNotNone(data['trace_id'])
    
    def test_response_includes_timestamp(self):
        """Test that all responses include timestamp."""
        response = self.client.get('/api/v1/health')
        data = json.loads(response.data)
        self.assertIn('timestamp', data)
        self.assertTrue(len(data['timestamp']) > 0)


class TestAuthenticationFlow(unittest.TestCase):
    """Test authentication flow."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app(":memory:")
        self.client = self.app.test_client()
    
    def test_auth_flow_requires_valid_user(self):
        """Test that authentication requires valid user."""
        response = self.client.post('/api/v1/auth/login', json={
            'username': 'nonexistent',
            'password': 'password'
        })
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertFalse(data['success'])


if __name__ == '__main__':
    unittest.main()
