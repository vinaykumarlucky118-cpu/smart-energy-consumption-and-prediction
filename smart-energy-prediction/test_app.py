"""
Comprehensive Test Suite for Smart Energy Prediction System with Authentication
"""

import os
import sys
import unittest
import json
import numpy as np

# Ensure root directory is on path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app, model, scaler
from database.db_setup import (
    init_db, insert_prediction, get_prediction_by_id,
    create_user, verify_user_credentials
)

class SmartEnergyAuthTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SECRET_KEY'] = 'test-secret-key'
        self.client = app.test_client()
        init_db()

    def test_ml_model_loaded(self):
        """Verify model and scaler are loaded properly."""
        self.assertIsNotNone(model, "Model must be loaded")
        self.assertIsNotNone(scaler, "Scaler must be loaded")

    def test_public_routes(self):
        """Verify public routes are accessible without login."""
        public_routes = ['/', '/about', '/login', '/register', '/api/dashboard-data']
        for r in public_routes:
            resp = self.client.get(r)
            self.assertEqual(resp.status_code, 200, f"Route {r} should be accessible publicly")

    def test_protected_routes_redirect_to_login(self):
        """Verify protected routes redirect unauthenticated users to login."""
        protected_routes = ['/predict', '/dashboard', '/history', '/model-performance']
        for r in protected_routes:
            resp = self.client.get(r, follow_redirects=False)
            self.assertEqual(resp.status_code, 302, f"Route {r} must redirect when unauthenticated")
            self.assertIn('/login', resp.headers['Location'])

    def test_login_success(self):
        """Test login with default demo admin credentials."""
        resp = self.client.post('/login', data={
            'email': 'admin@energy.ai',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Welcome back, System Administrator', resp.data)

    def test_login_failure(self):
        """Test login rejection with invalid credentials."""
        resp = self.client.post('/login', data={
            'email': 'admin@energy.ai',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Invalid email or password', resp.data)

    def test_user_registration_and_login(self):
        """Test new user registration."""
        unique_email = f"testuser_{os.getpid()}@energy.ai"
        resp = self.client.post('/register', data={
            'name': 'Test New User',
            'email': unique_email,
            'password': 'securepass123',
            'confirm_password': 'securepass123'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Account created!', resp.data)

    def test_authenticated_prediction(self):
        """Test making a prediction while logged in."""
        # 1. Login first
        self.client.post('/login', data={
            'email': 'student@energy.ai',
            'password': 'energy123'
        })
        
        # 2. Submit prediction
        payload = {
            'voltage': '230.0',
            'current': '5.5',
            'usage_hours': '7.0',
            'number_of_appliances': '5',
            'temperature': '29.0',
            'previous_consumption': '8.5'
        }
        resp = self.client.post('/predict', data=payload, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Prediction Result', resp.data)
        self.assertIn(b'kWh Predicted', resp.data)

    def test_logout(self):
        """Test user logout."""
        self.client.post('/login', data={
            'email': 'admin@energy.ai',
            'password': 'admin123'
        })
        resp = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'You have been signed out successfully', resp.data)

    def test_api_firebase_login(self):
        """Test Firebase token sync endpoint."""
        payload = {
            'email': 'firebase_tester@energy.ai',
            'name': 'Firebase Test User'
        }
        resp = self.client.post('/api/auth/firebase-login', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['user']['email'], 'firebase_tester@energy.ai')

    def test_bill_estimator(self):
        """Test bill estimator page and calculation."""
        self.client.post('/login', data={'email': 'student@energy.ai', 'password': 'energy123'})
        # GET request
        resp = self.client.get('/bill-estimator')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Electricity Bill Estimator', resp.data)
        
        # POST calculation
        resp = self.client.post('/bill-estimator', data={
            'energy_kwh': '250',
            'slab_type': 'slab_residential',
            'flat_rate': '6.0'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Estimated Bill', resp.data)

    def test_energy_simulator(self):
        """Test energy simulator page and scenario submission."""
        self.client.post('/login', data={'email': 'student@energy.ai', 'password': 'energy123'})
        # GET request
        resp = self.client.get('/simulator')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Energy Saving Simulator', resp.data)
        
        # POST simulation
        resp = self.client.post('/simulator', data={
            'action': 'simulate',
            'sim_name_0': 'Air Conditioner',
            'sim_power_0': '1500',
            'sim_qty_0': '1',
            'sim_current_hrs_0': '6.0',
            'sim_new_hrs_0': '4.0'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Projected Monthly Savings', resp.data)
        self.assertIn(b'Per-Appliance Savings Breakdown', resp.data)

if __name__ == '__main__':
    unittest.main(verbosity=2)

