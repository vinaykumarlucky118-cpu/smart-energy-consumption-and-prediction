"""
Test Suite for Upgraded EnerSense Platform Features
"""

import os
import sys
import unittest
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app, model, scaler
from database.db_setup import (
    init_db, get_advisor_history, get_weekly_consumption, verify_user_credentials
)
from utils.energy_utils import (
    calculate_power_kw, calculate_energy_kwh, calculate_energy_score,
    get_advisor_response
)

class EnerSenseFeaturesTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SECRET_KEY'] = 'test-secret-key-enersense'
        self.client = app.test_client()
        init_db()

    def login_student(self):
        return self.client.post('/login', data={
            'email': 'student@energy.ai',
            'password': 'energy123'
        }, follow_redirects=True)

    def test_advisor_page_access(self):
        """Test accessing the Energy Advisor page while logged in."""
        self.login_student()
        resp = self.client.get('/advisor')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'AI Energy Advisor', resp.data)
        self.assertIn(b'Frequently Asked Questions', resp.data)

    def test_api_advisor_chat(self):
        """Test sending a question to the Advisor API."""
        self.login_student()
        payload = {'question': 'How can I reduce my AC electricity consumption?'}
        resp = self.client.post('/api/advisor', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('answer', data)
        self.assertIn('24', data['answer'])

    def test_csv_export(self):
        """Test downloading CSV history."""
        self.login_student()
        resp = self.client.get('/api/export-csv')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, 'text/csv')
        self.assertIn('attachment;filename=enersense_history.csv', resp.headers.get('Content-Disposition', ''))
        self.assertIn(b'Voltage (V),Current (A)', resp.data)

    def test_weekly_data_api(self):
        """Test weekly data endpoint."""
        self.login_student()
        resp = self.client.get('/api/weekly-data')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertIsInstance(data['data'], list)

    def test_password_change(self):
        """Test updating user password in settings."""
        self.login_student()
        # Change password to 'newenergypass123'
        resp = self.client.post('/settings/change-password', data={
            'current_password': 'energy123',
            'new_password': 'newenergypass123',
            'confirm_new_password': 'newenergypass123'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Password updated successfully', resp.data)

        # Verify new credentials work
        user = verify_user_credentials('student@energy.ai', 'newenergypass123')
        self.assertIsNotNone(user)

        # Revert back to 'energy123'
        self.client.post('/settings/change-password', data={
            'current_password': 'newenergypass123',
            'new_password': 'energy123',
            'confirm_new_password': 'energy123'
        }, follow_redirects=True)
        user_restored = verify_user_credentials('student@energy.ai', 'energy123')
        self.assertIsNotNone(user_restored)

    def test_physics_calculations(self):
        """Verify physics power and energy formulas."""
        p_kw = calculate_power_kw(230.0, 5.0)
        self.assertEqual(p_kw, 1.15)
        e_kwh = calculate_energy_kwh(p_kw, 6.0)
        self.assertEqual(e_kwh, 6.90)

    def test_energy_score_scale(self):
        """Test Energy score logic bounded between 0 and 100."""
        score_good = calculate_energy_score(5.0, 4.0, 3, 22.0)
        self.assertTrue(0 <= score_good['score'] <= 100)
        self.assertEqual(score_good['status'], 'Excellent')

        score_high = calculate_energy_score(35.0, 18.0, 15, 38.0)
        self.assertTrue(0 <= score_high['score'] <= 100)
        self.assertIn(score_high['status'], ['Average', 'Needs Improvement'])

if __name__ == '__main__':
    unittest.main(verbosity=2)

