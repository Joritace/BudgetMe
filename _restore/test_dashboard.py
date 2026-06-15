from datetime import date, datetime

from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from budgetbuddy.models import BudgetCategory, BudgetProfile, Transaction
from budgetbuddy.mocks import get_mock_mobile_money, get_mock_user
from budgetbuddy.services import (
    build_dashboard_context,
    get_active_profile,
    get_expenses_for_profile,
    profile_to_user_dict,
    summarize_budget,
    transaction_to_dict,
)


def create_budget_via_form(client, name='Jane Doe', income=2_500_000, frequency='monthly', goal=400_000):
    """Helper: submit the budget setup form."""
    data = {
        'name': name,
        'income_amount': income,
        'income_frequency': frequency,
        'saving_goal_amount': goal,
        'form-TOTAL_FORMS': 2,
        'form-INITIAL_FORMS': 0,
        'form-MIN_NUM_FORMS': 0,
        'form-MAX_NUM_FORMS': 1000,
        'form-0-name': 'Rent',
        'form-0-allocated_amount': 800_000,
        'form-1-name': 'Food & Market',
        'form-1-allocated_amount': 450_000,
    }
    return client.post(reverse('budget_setup'), data)


class BudgetServiceTests(TestCase):
    def test_summarize_budget_calculates_totals(self):
        user = get_mock_user()
        expenses = [
            {'category': 'Rent', 'amount': 800_000},
            {'category': 'Food & Market', 'amount': 100_000},
        ]
        result = summarize_budget(user, expenses)
        self.assertEqual(result['total_spent'], 900_000)


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
    def test_new_user_redirected_to_setup(self):
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('budget_setup'))

    def test_budget_setup_saves_profile(self):
        response = create_budget_via_form(self.client)
        self.assertRedirects(response, reverse('dashboard'))
        profile = BudgetProfile.objects.get(name='Jane Doe')
        self.assertEqual(float(profile.income_amount), 2_500_000)
        self.assertEqual(profile.categories.count(), 2)

    def test_dashboard_after_setup(self):
        create_budget_via_form(self.client)
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'Jane Doe')
        self.assertContains(response, 'Rent')


class DashboardViewTests(TestCase):
    def setUp(self):
        create_budget_via_form(self.client)

    def test_dashboard_shows_income_frequency(self):
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'Monthly')

    def test_period_filter_weekly(self):
        response = self.client.get(reverse('dashboard'), {'period': 'weekly'})
        self.assertEqual(response.status_code, 200)

    def test_mobile_money_mock_uses_ugx(self):
        transaction = get_mock_mobile_money()
        self.assertEqual(transaction['currency'], 'UGX')
