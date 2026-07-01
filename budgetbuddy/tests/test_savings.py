from datetime import datetime, timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from budgetbuddy.models import BudgetCategory, BudgetProfile, SavingsDeposit, Transaction
from budgetbuddy.services.budget_period import get_budget_period
from budgetbuddy.services.savings import (
    create_manual_savings_deposit,
    ensure_periods_closed,
    get_spendable_balance,
    get_total_savings,
    savings_in_period,
)
from budgetbuddy.services.transfers import get_available_balance
from budgetbuddy.tests.helpers import login_test_user

TEST_STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


class SavingsServiceTests(TestCase):
    def setUp(self):
        self.profile = BudgetProfile.objects.create(
            name='Jane',
            income_amount=200_000,
            income_frequency='biweekly',
            saving_goal_amount=50_000,
        )
        BudgetCategory.objects.create(profile=self.profile, name='Food', allocated_amount=100_000)

    def test_manual_deposit_reduces_spendable_balance(self):
        create_manual_savings_deposit(self.profile, 30_000)
        balance = get_spendable_balance(self.profile)
        self.assertEqual(float(balance), 170_000)
        self.assertEqual(get_total_savings(self.profile), 30_000)

    def test_manual_deposit_counts_toward_period_savings_goal(self):
        create_manual_savings_deposit(self.profile, 20_000)
        period = get_budget_period(self.profile)
        self.assertEqual(savings_in_period(self.profile, period), 20_000)

    def test_cannot_save_more_than_available_balance(self):
        Transaction.objects.create(
            profile=self.profile,
            txn_type='expense',
            label='Food',
            category='Food',
            amount=150_000,
            occurred_at=timezone.now(),
        )
        with self.assertRaises(ValueError):
            create_manual_savings_deposit(self.profile, 100_000)

    def test_period_end_moves_remainder_to_savings(self):
        Transaction.objects.create(
            profile=self.profile,
            txn_type='expense',
            label='Food',
            category='Food',
            amount=50_000,
            occurred_at=timezone.now(),
        )
        period = get_budget_period(self.profile)
        past_date = period['start'] - timedelta(days=1)
        ensure_periods_closed(self.profile, on_date=past_date)
        self.assertFalse(
            SavingsDeposit.objects.filter(
                source=SavingsDeposit.PERIOD_END,
                period_start=period['start'],
            ).exists(),
        )

        future_date = period['end'] + timedelta(days=1)
        ensure_periods_closed(self.profile, on_date=future_date)
        deposit = SavingsDeposit.objects.get(
            source=SavingsDeposit.PERIOD_END,
            period_start=period['start'],
        )
        self.assertEqual(float(deposit.amount), 150_000)
        self.assertEqual(get_total_savings(self.profile), 150_000)

    def test_available_balance_matches_spendable_balance(self):
        create_manual_savings_deposit(self.profile, 25_000)
        self.assertEqual(get_available_balance(self.profile), get_spendable_balance(self.profile))


class SavingsViewTests(TestCase):
    def setUp(self):
        self.user = login_test_user(self.client)
        self.profile = BudgetProfile.objects.create(
            user=self.user,
            name='Jane Doe',
            income_amount=200_000,
            income_frequency='biweekly',
            saving_goal_amount=50_000,
        )
        BudgetCategory.objects.create(
            profile=self.profile,
            name='Food',
            allocated_amount=100_000,
        )

    @override_settings(STORAGES=TEST_STORAGES)
    def test_savings_page_loads(self):
        response = self.client.get(reverse('savings'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Total saved')
        self.assertContains(response, 'Add to savings')

    @override_settings(STORAGES=TEST_STORAGES)
    def test_post_adds_to_savings(self):
        response = self.client.post(reverse('savings'), {
            'amount': '30000',
            'note': 'SACCO',
        })
        self.assertEqual(response.status_code, 302)
        profile = BudgetProfile.objects.get(user=self.user)
        self.assertEqual(get_total_savings(profile), 30_000)
