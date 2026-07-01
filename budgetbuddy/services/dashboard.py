"""Dashboard assembly — greeting, insights, and transaction filtering."""

from datetime import date, datetime, timedelta

from django.utils import timezone

from budgetbuddy.services.budget_period import (
    default_transaction_period,
    get_budget_period,
    period_choices_for_frequency,
)
from budgetbuddy.services.page_context import build_guest_context

PERIOD_CHOICES = ('daily', 'weekly', 'biweekly', 'monthly')


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


def filter_transactions_by_period(transactions, period='monthly', profile=None):
    today = date.today()
    if period == 'daily':
        start = today
        end = today
    elif period == 'weekly':
        start = today - timedelta(days=6)
        end = today
    elif period == 'biweekly':
        if profile:
            budget_period = get_budget_period(profile)
            start = budget_period['start']
            end = budget_period['end']
        else:
            start = today - timedelta(days=13)
            end = today
    else:
        start = today.replace(day=1)
        end = today

    return [
        txn for txn in transactions
        if start <= _parse_transaction_date(txn) <= end
    ]


def get_insights(user, expenses, transactions, profile=None, budget_period=None):
    if budget_period is None and profile is not None:
        budget_period = get_budget_period(profile)

    if budget_period:
        from budgetbuddy.services.budget_period import filter_expenses_for_period
        period_expenses = filter_expenses_for_period(expenses, budget_period)
    else:
        period_expenses = expenses

    expense_totals = {}
    for expense in period_expenses:
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
        savings_saved = savings_progress(profile, period_expenses)
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


def build_empty_dashboard_context(request=None):
    user = getattr(request, 'user', None) if request is not None else None
    ctx = build_guest_context('home', greeting=get_greeting(), user=user)
    return ctx


def build_dashboard_context(user, expenses, transactions, period='monthly', mobile_money=None, profile=None):
    from budgetbuddy.services.budget import summarize_budget

    budget_period = get_budget_period(profile) if profile else None
    period_income = user.get('period_income') or user.get('income_amount', 0)
    allowed_periods = period_choices_for_frequency(user.get('income_frequency', 'monthly'))
    period = period if period in allowed_periods else default_transaction_period(
        user.get('income_frequency', 'monthly'),
    )

    filtered = filter_transactions_by_period(transactions, period, profile=profile)
    data = summarize_budget(user, expenses, period=budget_period)
    insights = get_insights(
        user, expenses, transactions, profile=profile, budget_period=budget_period,
    )

    budget_used_percent = round(
        (data['total_spent'] / period_income * 100)
        if period_income else 0,
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
        'period_choices': allowed_periods,
        'budget_period': budget_period,
        'budget_used_percent': min(budget_used_percent, 100),
        'total_expense': data['total_spent'],
        'total_balance': max(period_income - data['total_spent'], 0),
        'income_display': {
            'amount': user['income_amount'],
            'frequency': user['income_frequency_label'],
        },
    }
