"""Supabase Realtime API tests."""

from django.test import TestCase, override_settings
from django.urls import reverse

from budgetbuddy.tests.helpers import create_budget_via_form, login_test_user


SUPABASE_SETTINGS = {
    'SUPABASE_URL': 'https://example.supabase.co',
    'SUPABASE_ANON_KEY': 'test-anon-key',
    'SUPABASE_JWT_SECRET': 'test-jwt-secret-for-realtime',
    'SUPABASE_REALTIME_ENABLED': True,
}


@override_settings(**SUPABASE_SETTINGS)
class SupabaseRealtimeApiTests(TestCase):
    def test_token_requires_login(self):
        response = self.client.get(reverse('api_supabase_realtime_token'))
        self.assertEqual(response.status_code, 302)

    def test_token_returns_jwt_for_logged_in_user(self):
        login_test_user(self.client)
        response = self.client.get(reverse('api_supabase_realtime_token'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('token', data)
        self.assertTrue(len(data['token']) > 20)

    def test_token_disabled_when_not_configured(self):
        with override_settings(SUPABASE_REALTIME_ENABLED=False):
            login_test_user(self.client)
            response = self.client.get(reverse('api_supabase_realtime_token'))
            self.assertEqual(response.status_code, 404)

    def test_live_summary_for_budget_user(self):
        login_test_user(self.client)
        create_budget_via_form(self.client)
        response = self.client.get(reverse('api_live_summary'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['currency'], 'UGX')
        self.assertIn('total_balance', data)
        self.assertIn('available_balance', data)

    def test_live_summary_includes_deposits_html(self):
        login_test_user(self.client)
        create_budget_via_form(self.client)
        response = self.client.get(reverse('api_live_summary'), {'include': 'deposits'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('deposits_html', data)
