"""Dashboard assembly — greeting, insights, and transaction filtering."""

from datetime import date, datetime, timedelta

from django.utils import timezone

PERIOD_CHOICES = ('daily', 'weekly', 'monthly')
PERIOD_LABELS = {
    'daily': 'Daily',
    'weekly': 'Weekly',
    'monthly': 'Monthly',
}


def get_greeting():
    hour = timezone.localtime().hour
    if hour < 12:
        return 'Good Morning'
    if hour < 17:
        return 'Good Afternoon'
    return 'Good Evening'


def _parse_transaction_date(transaction):
    raw = transaction.get('datetime') or transaction.get('date')
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    return date.today()


def filter_transactions_by_period(transactions, period='monthly'):
    today = date.today()
    if period == 'daily':
        start = today
    elif period == 'weekly':
        start = today - timedelta(days=6)
    else:
        start = today.replace(day=1)

    return [
        txn for txn in transactions
        if _parse_transaction_date(txn) >= start
    ]


def get_insights(user, expenses, transactions, profile=None):
    expense_totals = {}
    for expense in expenses:
        category = expense.get('category', 'Other')
        expense_totals[category] = expense_totals.get(category, 0) + float(expense.get('amount', 0))

    if expense_totals:
        biggest_category = max(expense_totals, key=expense_totals.get)
        biggest_amount = expense_totals[biggest_category]
    else:
        biggest_category = '—'
        biggest_amount = 0

    today = date.today()
    week_start = today - timedelta(days=7)
    revenue_last_week = sum(
        float(txn.get('amount', 0))
        for txn in transactions
        if txn.get('type') == 'income' and _parse_transaction_date(txn) >= week_start
    )

    saving_goal_target = user.get('saving_goal_amount')
    if not saving_goal_target:
        saving_goal_target = user['budget_categories'].get('Savings (SACCO)', 0)

    if profile and profile.has_saving_goal:
        from budgetbuddy.services.profile import savings_progress
        savings_saved = savings_progress(profile, expenses)
        saving_goal_target = float(profile.saving_goal_amount)
    else:
        savings_saved = expense_totals.get('Savings (SACCO)', 0)

    saving_goal_percent = min(
        round((savings_saved / saving_goal_target * 100) if saving_goal_target else 0),
        100,
    )
    ring_circumference = 213.6
    ring_offset = round(ring_circumference - (ring_circumference * saving_goal_percent / 100), 2)

    return {
        'saving_goal_percent': saving_goal_percent,
        'saving_goal_target': round(saving_goal_target),
        'saving_goal_saved': round(savings_saved),
        'has_saving_goal': bool(user.get('saving_goal_amount') or saving_goal_target),
        'revenue_last_week': round(revenue_last_week),
        'biggest_expense_category': biggest_category,
        'biggest_expense_amount': round(biggest_amount),
        'ring_offset': ring_offset,
    }


def build_empty_dashboard_context():
    return {
        'has_budget': False,
        'greeting': get_greeting(),
        'first_name': 'Friend',
        'user': {'name': 'Guest'},
        'data': {'currency': 'UGX'},
    }


def build_dashboard_context(user, expenses, transactions, period='monthly', mobile_money=None, profile=None):
    from budgetbuddy.services.budget import summarize_budget

    period = period if period in PERIOD_CHOICES else 'monthly'
    filtered = filter_transactions_by_period(transactions, period)
    data = summarize_budget(user, expenses)
    insights = get_insights(user, expenses, transactions, profile=profile)

    budget_used_percent = round(
        (data['total_spent'] / user['monthly_income'] * 100)
        if user['monthly_income'] else 0,
        1,
    )

    first_name = user['name'].split()[0] if user.get('name') else 'Friend'

    return {
        'has_budget': True,
        'user': user,
        'data': data,
        'insights': insights,
        'transactions': filtered,
        'mobile_money': mobile_money,
        'greeting': get_greeting(),
        'first_name': first_name,
        'period': period,
        'period_choices': PERIOD_LABELS,
        'budget_used_percent': min(budget_used_percent, 100),
        'total_expense': data['total_spent'],
        'total_balance': max(user['monthly_income'] - data['total_spent'], 0),
        'income_display': {
            'amount': user['income_amount'],
            'frequency': user['income_frequency_label'],
            'monthly_equivalent': user['monthly_income'],
        },
    }
