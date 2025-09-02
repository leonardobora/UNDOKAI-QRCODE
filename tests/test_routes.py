"""
Unit tests for Flask routes and API endpoints.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from flask import url_for

from models import Participant, CheckIn, DeliveryItem, DeliveryLog, Dependent
from app import db


class TestUserRoutes:
    """Test cases for user-facing routes."""
    
    def test_user_index(self, client, test_app):
        """Test user homepage."""
        with test_app.app_context():
            response = client.get('/')
            assert response.status_code == 200
            assert b'total_participants' in response.data
    
    def test_user_index_with_data(self, client, test_app, db_with_data):
        """Test user homepage with sample data."""
        with test_app.app_context():
            data = db_with_data
            response = client.get('/')
            assert response.status_code == 200
    
    def test_qr_lookup_page(self, client, test_app):
        """Test QR lookup page."""
        with test_app.app_context():
            response = client.get('/user/qr-lookup')
            assert response.status_code == 200


class TestAdminAuthentication:
    """Test cases for admin authentication."""
    
    def test_admin_login_page(self, client, test_app):
        """Test admin login page GET request."""
        with test_app.app_context():
            response = client.get('/admin/login')
            assert response.status_code == 200
    
    @patch('auth.check_admin_credentials')
    def test_admin_login_success(self, mock_check_creds, client, test_app):
        """Test successful admin login."""
        with test_app.app_context():
            mock_check_creds.return_value = True
            
            response = client.post('/admin/login', data={
                'username': 'admin',
                'password': 'password'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            mock_check_creds.assert_called_once_with('admin', 'password')
    
    @patch('auth.check_admin_credentials')
    def test_admin_login_failure(self, mock_check_creds, client, test_app):
        """Test failed admin login."""
        with test_app.app_context():
            mock_check_creds.return_value = False
            
            response = client.post('/admin/login', data={
                'username': 'wrong',
                'password': 'wrong'
            })
            
            assert response.status_code == 200
            mock_check_creds.assert_called_once_with('wrong', 'wrong')
    
    def test_admin_logout(self, client, test_app):
        """Test admin logout."""
        with test_app.app_context():
            # Login first
            with client.session_transaction() as sess:
                sess['admin_logged_in'] = True
                sess['admin_username'] = 'admin'
            
            response = client.get('/admin/logout', follow_redirects=True)
            assert response.status_code == 200
    
    def test_admin_protected_route_without_login(self, client, test_app):
        """Test accessing admin route without login."""
        with test_app.app_context():
            response = client.get('/admin')
            # Should redirect to login
            assert response.status_code == 302


class TestAdminRoutes:
    """Test cases for admin routes."""
    
    def test_admin_index_authenticated(self, client, test_app):
        """Test admin homepage when authenticated."""
        with test_app.app_context():
            # Simulate logged in session
            with client.session_transaction() as sess:
                sess['admin_logged_in'] = True
                sess['admin_username'] = 'admin'
            
            response = client.get('/admin')
            assert response.status_code == 200
    
    def test_admin_panel_authenticated(self, client, test_app):
        """Test admin panel when authenticated."""
        with test_app.app_context():
            # Simulate logged in session
            with client.session_transaction() as sess:
                sess['admin_logged_in'] = True
                sess['admin_username'] = 'admin'
            
            response = client.get('/admin/panel')
            assert response.status_code == 200
    
    def test_entregas_list_authenticated(self, client, test_app, db_with_data):
        """Test deliveries list when authenticated."""
        with test_app.app_context():
            data = db_with_data
            
            # Simulate logged in session
            with client.session_transaction() as sess:
                sess['admin_logged_in'] = True
                sess['admin_username'] = 'admin'
            
            response = client.get('/entregas')
            assert response.status_code == 200


class TestRegistrationRoutes:
    """Test cases for participant registration."""
    
    def test_register_page_get(self, client, test_app):
        """Test registration page GET request."""
        with test_app.app_context():
            response = client.get('/register')
            assert response.status_code == 200
    
    def test_register_participant_success(self, client, test_app):
        """Test successful participant registration."""
        with test_app.app_context():
            response = client.post('/register', data={
                'nome': 'João Silva',
                'email': 'joao.silva@lightera.com',
                'telefone': '11999887766',
                'departamento': 'TI',
                'matricula': '12345',
                'dependente_1_nome': 'Maria Silva',
                'dependente_1_idade': '8'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            
            # Verify participant was created
            participant = Participant.query.filter_by(email='joao.silva@lightera.com').first()
            assert participant is not None
            assert participant.nome == 'João Silva'
            assert len(participant.dependents) == 1
            assert participant.dependents[0].nome == 'Maria Silva'
    
    def test_register_participant_duplicate_email(self, client, test_app):
        """Test registration with duplicate email."""
        with test_app.app_context():
            # Create first participant
            participant1 = Participant(
                nome='First User',
                email='duplicate@lightera.com',
                qr_code='QR001'
            )
            db.session.add(participant1)
            db.session.commit()
            
            # Try to register with same email
            response = client.post('/register', data={
                'nome': 'Second User',
                'email': 'duplicate@lightera.com',
                'telefone': '11999887766',
                'departamento': 'TI'
            })
            
            # Should handle the error gracefully
            assert response.status_code in [200, 302]  # Either show form with error or redirect
    
    def test_success_page(self, client, test_app, sample_participant):
        """Test participant success page."""
        with test_app.app_context():
            db.session.add(sample_participant)
            db.session.commit()
            
            response = client.get(f'/success/{sample_participant.id}')
            assert response.status_code == 200


class TestCheckinRoutes:
    """Test cases for check-in related routes."""
    
    def test_scanner_page(self, client, test_app):
        """Test QR scanner page."""
        with test_app.app_context():
            response = client.get('/scanner')
            assert response.status_code == 200
    
    def test_checkin_search_page(self, client, test_app):
        """Test check-in search page."""
        with test_app.app_context():
            response = client.get('/checkin/search')
            assert response.status_code == 200
    
    def test_dashboard_authenticated(self, client, test_app):
        """Test dashboard when authenticated."""
        with test_app.app_context():
            # Simulate logged in session
            with client.session_transaction() as sess:
                sess['admin_logged_in'] = True
                sess['admin_username'] = 'admin'
            
            response = client.get('/dashboard')
            assert response.status_code == 200


class TestAPIRoutes:
    """Test cases for API endpoints."""
    
    def test_lookup_participant_by_email_success(self, client, test_app, sample_participant):
        """Test successful participant lookup by email."""
        with test_app.app_context():
            db.session.add(sample_participant)
            db.session.commit()
            
            response = client.post('/api/lookup_participant_by_email', 
                                 json={'email': 'joao.silva@lightera.com'})
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['success'] is True
            assert data['participant']['nome'] == 'João Silva'
    
    def test_lookup_participant_by_email_not_found(self, client, test_app):
        """Test participant lookup with non-existent email."""
        with test_app.app_context():
            response = client.post('/api/lookup_participant_by_email', 
                                 json={'email': 'notfound@lightera.com'})
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['success'] is False
            assert 'não encontrado' in data['message'].lower()
    
    def test_validate_qr_success(self, client, test_app, sample_participant):
        """Test successful QR code validation."""
        with test_app.app_context():
            db.session.add(sample_participant)
            db.session.commit()
            
            response = client.post('/api/validate_qr', 
                                 json={'qr_code': 'QR123456'})
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['success'] is True
            assert data['participant']['nome'] == 'João Silva'
            
            # Verify check-in was created
            checkin = CheckIn.query.filter_by(participant_id=sample_participant.id).first()
            assert checkin is not None
    
    def test_validate_qr_invalid_code(self, client, test_app):
        """Test QR validation with invalid code."""
        with test_app.app_context():
            response = client.post('/api/validate_qr', 
                                 json={'qr_code': 'INVALID123'})
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['success'] is False
            assert 'inválido' in data['message'].lower()
    
    def test_validate_qr_duplicate_checkin(self, client, test_app, sample_participant):
        """Test QR validation for already checked-in participant."""
        with test_app.app_context():
            db.session.add(sample_participant)
            db.session.flush()
            
            # Create existing check-in
            existing_checkin = CheckIn(participant_id=sample_participant.id)
            db.session.add(existing_checkin)
            db.session.commit()
            
            response = client.post('/api/validate_qr', 
                                 json={'qr_code': 'QR123456'})
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['success'] is False
            assert 'já fez check-in' in data['message']
    
    def test_search_participant_by_name(self, client, test_app, sample_participant):
        """Test participant search by name."""
        with test_app.app_context():
            db.session.add(sample_participant)
            db.session.commit()
            
            response = client.get('/api/search_participant?q=João')
            assert response.status_code == 200
            
            data = response.get_json()
            assert len(data) == 1
            assert data[0]['nome'] == 'João Silva'
    
    def test_search_participant_no_results(self, client, test_app):
        """Test participant search with no results."""
        with test_app.app_context():
            response = client.get('/api/search_participant?q=NonExistent')
            assert response.status_code == 200
            
            data = response.get_json()
            assert len(data) == 0
    
    def test_manual_checkin_success(self, client, test_app, sample_participant):
        """Test successful manual check-in."""
        with test_app.app_context():
            db.session.add(sample_participant)
            db.session.commit()
            
            response = client.post('/api/manual_checkin', 
                                 json={'participant_id': sample_participant.id})
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['success'] is True
            
            # Verify check-in was created
            checkin = CheckIn.query.filter_by(participant_id=sample_participant.id).first()
            assert checkin is not None
    
    def test_manual_checkin_invalid_participant(self, client, test_app):
        """Test manual check-in with invalid participant."""
        with test_app.app_context():
            response = client.post('/api/manual_checkin', 
                                 json={'participant_id': 99999})
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['success'] is False
            assert 'não encontrado' in data['message'].lower()
    
    def test_dashboard_stats_api(self, client, test_app, db_with_data):
        """Test dashboard statistics API."""
        with test_app.app_context():
            data = db_with_data
            
            response = client.get('/api/dashboard_stats')
            assert response.status_code == 200
            
            stats = response.get_json()
            assert 'total_participants' in stats
            assert 'total_checkins' in stats
            assert 'pending_checkins' in stats
            assert stats['total_participants'] == 1
            assert stats['total_checkins'] == 1


class TestDeliveryRoutes:
    """Test cases for delivery-related routes."""
    
    def test_delivery_page_authenticated(self, client, test_app):
        """Test delivery page when authenticated."""
        with test_app.app_context():
            # Simulate logged in session
            with client.session_transaction() as sess:
                sess['admin_logged_in'] = True
                sess['admin_username'] = 'admin'
            
            response = client.get('/delivery')
            assert response.status_code == 200
    
    def test_inventory_page_authenticated(self, client, test_app):
        """Test inventory page when authenticated."""
        with test_app.app_context():
            # Simulate logged in session
            with client.session_transaction() as sess:
                sess['admin_logged_in'] = True
                sess['admin_username'] = 'admin'
            
            response = client.get('/inventory')
            assert response.status_code == 200


class TestHealthEndpoint:
    """Test cases for health check endpoint."""
    
    def test_health_endpoint(self, client, test_app):
        """Test health check endpoint."""
        with test_app.app_context():
            response = client.get('/health')
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['status'] == 'healthy'
            assert 'database' in data
            assert 'timestamp' in data


class TestErrorHandling:
    """Test cases for error handling."""
    
    def test_404_error(self, client, test_app):
        """Test 404 error handling."""
        with test_app.app_context():
            response = client.get('/nonexistent-page')
            assert response.status_code == 404
    
    def test_api_missing_data(self, client, test_app):
        """Test API endpoint with missing data."""
        with test_app.app_context():
            # POST request without required JSON data
            response = client.post('/api/validate_qr', json={})
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['success'] is False
    
    def test_api_invalid_json(self, client, test_app):
        """Test API endpoint with invalid JSON."""
        with test_app.app_context():
            response = client.post('/api/validate_qr', 
                                 data='invalid json',
                                 content_type='application/json')
            assert response.status_code == 400


class TestRouteIntegration:
    """Integration tests for multiple routes working together."""
    
    def test_complete_participant_flow(self, client, test_app):
        """Test complete participant flow from registration to check-in."""
        with test_app.app_context():
            # 1. Register participant
            response = client.post('/register', data={
                'nome': 'Integration Test User',
                'email': 'integration@lightera.com',
                'telefone': '11999887766',
                'departamento': 'Test',
                'matricula': '99999'
            }, follow_redirects=True)
            assert response.status_code == 200
            
            # 2. Find the created participant
            participant = Participant.query.filter_by(email='integration@lightera.com').first()
            assert participant is not None
            
            # 3. Test QR lookup
            response = client.post('/api/lookup_participant_by_email', 
                                 json={'email': 'integration@lightera.com'})
            data = response.get_json()
            assert data['success'] is True
            qr_code = data['participant']['qr_code']
            
            # 4. Test QR validation (check-in)
            response = client.post('/api/validate_qr', 
                                 json={'qr_code': qr_code})
            data = response.get_json()
            assert data['success'] is True
            
            # 5. Verify check-in was recorded
            checkin = CheckIn.query.filter_by(participant_id=participant.id).first()
            assert checkin is not None
            
            # 6. Test dashboard stats reflect the changes
            response = client.get('/api/dashboard_stats')
            stats = response.get_json()
            assert stats['total_participants'] >= 1
            assert stats['total_checkins'] >= 1
    
    def test_admin_workflow(self, client, test_app, db_with_data):
        """Test admin workflow."""
        with test_app.app_context():
            data = db_with_data
            
            # 1. Login as admin
            with client.session_transaction() as sess:
                sess['admin_logged_in'] = True
                sess['admin_username'] = 'admin'
            
            # 2. Access admin dashboard
            response = client.get('/admin')
            assert response.status_code == 200
            
            # 3. Access admin panel
            response = client.get('/admin/panel')
            assert response.status_code == 200
            
            # 4. Access delivery management
            response = client.get('/entregas')
            assert response.status_code == 200
            
            # 5. Access main dashboard
            response = client.get('/dashboard')
            assert response.status_code == 200
            
            # 6. Check stats API
            response = client.get('/api/dashboard_stats')
            assert response.status_code == 200
            
            # 7. Logout
            response = client.get('/admin/logout', follow_redirects=True)
            assert response.status_code == 200