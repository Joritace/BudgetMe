from datetime import date, datetime

from budgetbuddy.constants import (
    CURRENCY_CODE,
    DEFAULT_BUDGET_CATEGORIES,
    MOBILE_MONEY_PROVIDERS,
)


def get_mock_user(user_id=None):
    return {
        'id': user_id or 1,
        'name': 'Sarah Nakato',
        'monthly_income': 2_500_000,
        'income_amount': 2_500_000,
        'income_frequency': 'monthly',
        'income_frequency_label': 'Monthly',
        'saving_goal_amount': 400_000,
        'currency': CURRENCY_CODE,
        'budget_categories': dict(DEFAULT_BUDGET_CATEGORIES),
    }


def get_mock_expenses(user_id=None, year=None, month=None):
    today = date.today()
    return [
        {'date': today.replace(day=1), 'category': 'Rent', 'amount': 800_000},
        {'date': today.replace(day=3), 'category': 'Food & Market', 'amount': 185_000},
        {'date': today.replace(day=5), 'category': 'Transport', 'amount': 45_000},
        {'date': today.replace(day=7), 'category': 'Utilities', 'amount': 120_000},
        {'date': today.replace(day=10), 'category': 'Airtime & Data', 'amount': 30_000},
        {'date': today.replace(day=12), 'category': 'School Fees', 'amount': 300_000},
        {'date': today.replace(day=15), 'category': 'Savings (SACCO)', 'amount': 400_000},
        {'date': today.replace(day=18), 'category': 'Health', 'amount': 75_000},
        {'date': today.replace(day=20), 'category': 'Entertainment', 'amount': 50_000},
    ]


def get_mock_transactions(user_id=None):
    today = date.today()
    return [
        {
            'type': 'income',
            'label': 'Salary',
            'category': 'Salary',
            'amount': 2_500_000,
            'datetime': datetime(today.year, today.month, min(today.day, 28), 18, 27),
            'icon': 'salary',
        },
        {
            'type': 'expense',
            'label': 'Rent',
            'category': 'Rent',
            'amount': 800_000,
            'datetime': datetime(today.year, today.month, min(15, today.day or 1), 8, 30),
            'icon': 'rent',
        },
        {
            'type': 'expense',
            'label': 'Food & Market',
            'category': 'Food & Market',
            'amount': 185_000,
            'datetime': datetime(today.year, today.month, min(10, today.day or 1), 12, 15),
            'icon': 'food',
        },
        {
            'type': 'expense',
            'label': 'Transport',
            'category': 'Transport',
            'amount': 45_000,
            'datetime': datetime(today.year, today.month, min(8, today.day or 1), 7, 45),
            'icon': 'transport',
        },
        {
            'type': 'expense',
            'label': 'Airtime & Data',
            'category': 'Airtime & Data',
            'amount': 30_000,
            'datetime': datetime(today.year, today.month, min(5, today.day or 1), 16, 0),
            'icon': 'airtime',
        },
        {
            'type': 'income',
            'label': 'Mobile Money',
            'category': 'Mobile Money',
            'amount': 120_000,
            'datetime': datetime(today.year, today.month, min(3, today.day or 1), 14, 20),
            'icon': 'mobile_money',
        },
        {
            'type': 'expense',
            'label': 'School Fees',
            'category': 'School Fees',
            'amount': 300_000,
            'datetime': datetime(today.year, today.month, min(12, today.day or 1), 9, 0),
            'icon': 'school',
        },
    ]


def get_mock_mobile_money(user_id=None):
    return {
        'provider': MOBILE_MONEY_PROVIDERS['mtn'],
        'transaction_id': 'MM20250612001',
        'phone_number': '+256770123456',
        'amount': 120_000,
        'currency': CURRENCY_CODE,
        'status': 'completed',
        'timestamp': date.today().isoformat(),
        'user_id': user_id or 1,
    }
