from datetime import date, datetime

from django.contrib.sites.models import Site
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from allauth.socialaccount.models import SocialApp

from budgetbuddy.models import BudgetCategory, BudgetProfile, MobileMoneyTransaction, Transaction
from budgetbuddy.mocks import get_mock_mobile_money, get_mock_transactions, get_mock_user
from budgetbuddy.services import (
    build_dashboard_context,
    build_empty_dashboard_context,
    profile_to_user_dict,
    summarize_budget,
    transaction_to_dict,
)
from budgetbuddy.tests.helpers import budget_setup_post_data, create_budget_via_form, login_test_user, set_profile_phones


def enable_google_oauth_for_tests():
    site = Site.objects.get_current()
    app, _ = SocialApp.objects.update_or_create(
        provider='google',
        defaults={
            'name': 'Google',
            'client_id': 'test-client-id.apps.googleusercontent.com',
            'secret': 'test-client-secret',
        },
    )
    app.sites.add(site)
    return app

class BudgetServiceTests(TestCase):
    def test_summarize_budget_calculates_totals(self):
        user = get_mock_user()
        expenses = [
            {'category': 'Rent', 'amount': 800_000},
            {'category': 'Food & Market', 'amount': 100_000},
        ]
        result = summarize_budget(user, expenses)
        self.assertEqual(result['currency'], 'UGX')
        self.assertEqual(result['total_spent'], 900_000)
        self.assertGreater(result['total_allocated'], 0)


class DashboardServiceTests(TestCase):
    def test_build_dashboard_context_includes_insights(self):
        user = get_mock_user()
        expenses = [{'category': 'Rent', 'amount': 800_000}]
        transactions = get_mock_transactions()
        ctx = build_dashboard_context(user, expenses, transactions)
        self.assertIn('greeting', ctx)
        self.assertIn('insights', ctx)
        self.assertIn('saving_goal_percent', ctx['insights'])
        self.assertEqual(ctx['data']['currency'], 'UGX')

    def test_empty_dashboard_context(self):
        ctx = build_empty_dashboard_context()
        self.assertFalse(ctx['has_budget'])
        self.assertIn('greeting', ctx)
        self.assertIn('nav_items', ctx)


class ProfileServiceTests(TestCase):
    def test_profile_monthly_income_daily(self):
        profile = BudgetProfile.objects.create(
            name='Test',
            income_amount=100_000,
            income_frequency='daily',
        )
        self.assertEqual(float(profile.normalized_monthly_income()), 3_000_000)

    def test_profile_monthly_income_biweekly(self):
        profile = BudgetProfile.objects.create(
            name='Test',
            income_amount=1_000_000,
            income_frequency='biweekly',
        )
        monthly = float(profile.normalized_monthly_income())
        self.assertAlmostEqual(monthly, 1_000_000 * 26 / 12, places=0)

    def test_profile_to_user_dict(self):
        profile = BudgetProfile.objects.create(
            name='Jane',
            income_amount=2_500_000,
            income_frequency='monthly',
            saving_goal_amount=500_000,
        )
        BudgetCategory.objects.create(profile=profile, name='Rent', allocated_amount=800_000)
        user = profile_to_user_dict(profile)
        self.assertEqual(user['saving_goal_amount'], 500_000)
        self.assertEqual(user['monthly_income'], 2_500_000)


class TransactionServiceTests(TestCase):
    def setUp(self):
        self.profile = BudgetProfile.objects.create(
            name='Jane',
            income_amount=2_500_000,
            income_frequency='monthly',
        )

    def _create_transaction(self, txn_type, label, category, amount, day=1):
        occurred_at = timezone.make_aware(
            datetime.combine(date.today().replace(day=day), datetime.min.time())
        )
        return Transaction.objects.create(
            profile=self.profile,
            txn_type=txn_type,
            label=label,
            category=category,
            amount=amount,
            occurred_at=occurred_at,
        )

    def test_transaction_to_dict(self):
        txn = self._create_transaction('expense', 'Rent', 'Rent', 800_000)
        data = transaction_to_dict(txn)
        self.assertEqual(data['icon'], 'rent')


class BudgetSetupViewTests(TestCase):
    def test_empty_dashboard_prompts_sign_in_for_guest(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign in')
        self.assertContains(response, 'Where did my money go')
        self.assertNotContains(response, 'sidebar-nav')

    def test_empty_dashboard_shows_google_when_configured(self):
        enable_google_oauth_for_tests()
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'Continue with Google')
        self.assertNotContains(response, 'sidebar-nav')

    def test_empty_dashboard_shows_setup_cta_when_logged_in(self):
        login_test_user(self.client)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Set up your budget')

    def test_budget_setup_requires_login(self):
        response = self.client.get(reverse('budget_setup'))
        self.assertRedirects(
            response,
            f'{reverse("account_login")}?next={reverse("budget_setup")}',
        )

    def test_login_page_shows_google_option(self):
        enable_google_oauth_for_tests()
        response = self.client.get(reverse('account_login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Continue with Google')
        self.assertContains(response, 'Sign in')

    def test_auth_status_for_guest(self):
        response = self.client.get(reverse('auth_status'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['authenticated'])

    def test_auth_status_for_logged_in_user(self):
        login_test_user(self.client)
        response = self.client.get(reverse('auth_status'))
        self.assertTrue(response.json()['authenticated'])

    def test_html_responses_are_not_cached(self):
        response = self.client.get(reverse('dashboard'))
        self.assertIn('no-store', response['Cache-Control'])

    def test_login_page_shows_setup_notice_without_google(self):
        response = self.client.get(reverse('account_login'))
        self.assertContains(response, 'Google sign-in needs setup')
        self.assertContains(response, 'Sign in')

    def test_budget_setup_saves_profile(self):
        response = create_budget_via_form(self.client)
        self.assertRedirects(response, reverse('dashboard'))
        profile = BudgetProfile.objects.get(name='Jane Doe')
        self.assertEqual(float(profile.income_amount), 2_500_000)
        self.assertEqual(profile.categories.count(), 2)
        self.assertIsNotNone(profile.user)

    def test_budget_setup_edit_shows_delete_option(self):
        create_budget_via_form(self.client)
        response = self.client.get(reverse('budget_setup'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Delete budget')
        self.assertContains(response, reverse('budget_delete'))

    def test_budget_rejects_over_income(self):
        login_test_user(self.client)
        response = self.client.post(
            reverse('budget_setup'),
            budget_setup_post_data(income=1_000_000),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'cannot exceed your monthly income')
        self.assertEqual(BudgetProfile.objects.count(), 0)

    def test_budget_delete_removes_profile(self):
        create_budget_via_form(self.client)
        profile = BudgetProfile.objects.get(name='Jane Doe')
        response = self.client.post(reverse('budget_delete'))
        self.assertRedirects(response, reverse('dashboard'))
        self.assertFalse(BudgetProfile.objects.filter(pk=profile.pk).exists())

    def test_home_link_points_to_dashboard(self):
        login_test_user(self.client)
        response = self.client.get(reverse('budget_setup'))
        self.assertContains(response, f'href="{reverse("dashboard")}"')


class DashboardViewTests(TestCase):
    def setUp(self):
        create_budget_via_form(self.client)

    def test_dashboard_shows_user_data(self):
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'Jane')
        self.assertContains(response, 'Rent')
        self.assertContains(response, 'Total Expense')
        self.assertContains(response, 'Total Balance')
        self.assertContains(response, 'Saving Goal')
        self.assertContains(response, 'Monthly Budget')
        self.assertContains(response, 'Allocated')
        self.assertContains(response, 'Delete budget')

    def test_period_filter_weekly(self):
        response = self.client.get(reverse('dashboard'), {'period': 'weekly'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Weekly')

    def test_mobile_money_mock_uses_ugx(self):
        transaction = get_mock_mobile_money()
        self.assertEqual(transaction['currency'], 'UGX')


class TransferViewTests(TestCase):
    def setUp(self):
        create_budget_via_form(self.client)
        set_profile_phones(self.client)

    def test_transfer_page_renders(self):
        response = self.client.get(reverse('transfer'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Record expense')
        self.assertContains(response, 'Available this month')
        self.assertContains(response, 'Deposit or spend')

    def test_transfer_cash_spend_custom_amount(self):
        response = self.client.post(reverse('transfer'), {
            'direction': 'withdraw',
            'provider': 'cash',
            'amount': 47_500,
            'category': 'Rent',
        })
        self.assertRedirects(response, reverse('transfer'))
        mm = MobileMoneyTransaction.objects.first()
        self.assertEqual(float(mm.amount), 47_500)

    def test_transfer_cash_spend(self):
        response = self.client.post(reverse('transfer'), {
            'direction': 'withdraw',
            'provider': 'cash',
            'amount': 50_000,
            'category': 'Rent',
            'note': 'Market run',
        })
        self.assertRedirects(response, reverse('transfer'))
        self.assertEqual(MobileMoneyTransaction.objects.count(), 1)
        mm = MobileMoneyTransaction.objects.first()
        self.assertEqual(mm.provider, 'cash')
        self.assertEqual(mm.phone_number, '')

    def test_transfer_mtn_spend(self):
        response = self.client.post(reverse('transfer'), {
            'direction': 'withdraw',
            'provider': 'mtn',
            'amount': 50_000,
            'category': 'Rent',
        })
        self.assertRedirects(response, reverse('transfer'))
        mm = MobileMoneyTransaction.objects.first()
        self.assertTrue(mm.phone_number.startswith('+256'))

    def test_transfer_deposit(self):
        response = self.client.post(reverse('transfer'), {
            'direction': 'deposit',
            'provider': 'cash',
            'amount': 100_000,
            'category': 'Rent',
        })
        self.assertRedirects(response, reverse('transfer'))
        txn = Transaction.objects.filter(txn_type='income').first()
        self.assertIsNotNone(txn)

    def test_transfer_requires_profile_phone_for_mtn(self):
        profile = BudgetProfile.objects.get(name='Jane Doe')
        profile.mtn_phone = ''
        profile.save()
        response = self.client.post(reverse('transfer'), {
            'direction': 'withdraw',
            'provider': 'mtn',
            'amount': 50_000,
            'category': 'Rent',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Profile')


class ProfileViewTests(TestCase):
    def setUp(self):
        create_budget_via_form(self.client)

    def test_profile_page_renders(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jane Doe')
        self.assertContains(response, 'Mobile money numbers')

    def test_profile_saves_phones(self):
        response = set_profile_phones(self.client)
        self.assertRedirects(response, reverse('profile'))
        profile = BudgetProfile.objects.get(name='Jane Doe')
        self.assertTrue(profile.mtn_phone.startswith('+256'))

    def test_profile_empty_without_budget(self):
        login_test_user(self.client)
        BudgetProfile.objects.all().delete()
        response = self.client.get(reverse('profile'))
        self.assertContains(response, 'Set up your budget first')
