from decimal import Decimal

from django.conf import settings
from django.db import models

from budgetbuddy.constants import CURRENCY_CODE, INCOME_FREQUENCY_CHOICES


class BudgetProfile(models.Model):
    """A user's budget plan — income, saving goal, and category limits."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='budget_profile',
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=150)
    income_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    income_frequency = models.CharField(
        max_length=10,
        choices=INCOME_FREQUENCY_CHOICES,
        default='monthly',
    )
    saving_goal_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        null=True,
        blank=True,
    )
    monthly_income = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    currency = models.CharField(max_length=3, default=CURRENCY_CODE)
    mtn_phone = models.CharField(max_length=15, blank=True, default='')
    airtel_phone = models.CharField(max_length=15, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.name} ({self.currency} {self.income_amount}/{self.income_frequency})'

    def normalized_monthly_income(self):
        amount = Decimal(self.income_amount or 0)
        if self.income_frequency == 'daily':
            return amount * Decimal('30')
        if self.income_frequency == 'biweekly':
            return (amount * Decimal('26')) / Decimal('12')
        return amount

    def save(self, *args, **kwargs):
        self.monthly_income = self.normalized_monthly_income()
        super().save(*args, **kwargs)

    @property
    def income_frequency_label(self):
        return dict(INCOME_FREQUENCY_CHOICES).get(self.income_frequency, self.income_frequency)

    @property
    def has_saving_goal(self):
        return self.saving_goal_amount is not None and self.saving_goal_amount > 0


class BudgetCategory(models.Model):
    profile = models.ForeignKey(
        BudgetProfile,
        on_delete=models.CASCADE,
        related_name='categories',
    )
    name = models.CharField(max_length=100)
    allocated_amount = models.DecimalField(max_digits=12, decimal_places=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['profile', 'name'], name='unique_category_per_profile'),
        ]
        ordering = ['name']

    def __str__(self):
        return f'{self.name}: {self.allocated_amount}'


class Expense(models.Model):
    profile = models.ForeignKey(
        BudgetProfile,
        on_delete=models.CASCADE,
        related_name='expenses',
    )
    category = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    date = models.DateField()
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f'{self.category} — {self.amount} on {self.date}'


class Transaction(models.Model):
    INCOME = 'income'
    EXPENSE = 'expense'
    TYPE_CHOICES = [
        (INCOME, 'Income'),
        (EXPENSE, 'Expense'),
    ]

    profile = models.ForeignKey(
        BudgetProfile,
        on_delete=models.CASCADE,
        related_name='transactions',
    )
    txn_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    label = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    occurred_at = models.DateTimeField()
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-occurred_at']

    def __str__(self):
        sign = '+' if self.txn_type == self.INCOME else '-'
        return f'{self.label} {sign}{self.currency} {self.amount}'

    @property
    def currency(self):
        return self.profile.currency


class MobileMoneyTransaction(models.Model):
    PROVIDER_CHOICES = [
        ('mtn', 'MTN Mobile Money'),
        ('airtel', 'Airtel Money'),
        ('cash', 'Cash'),
    ]
    DIRECTION_CHOICES = [
        ('withdraw', 'Spend'),
        ('deposit', 'Deposit'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    profile = models.ForeignKey(
        BudgetProfile,
        on_delete=models.CASCADE,
        related_name='mobile_money_transactions',
    )
    provider = models.CharField(max_length=10, choices=PROVIDER_CHOICES)
    direction = models.CharField(
        max_length=10,
        choices=DIRECTION_CHOICES,
        default='withdraw',
    )
    transaction_id = models.CharField(max_length=64, unique=True)
    phone_number = models.CharField(max_length=15, blank=True, default='')
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    currency = models.CharField(max_length=3, default=CURRENCY_CODE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.get_provider_display()} — {self.currency} {self.amount}'
