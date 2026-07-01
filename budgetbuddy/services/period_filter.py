"""Shared date windows for period filters."""

from datetime import date, timedelta

from budgetbuddy.services.budget_period import get_budget_period


def transaction_window(profile, period):
    today = date.today()
    if period == 'daily':
        return today, today
    if period == 'weekly':
        return today - timedelta(days=6), today
    if period == 'biweekly':
        budget_period = get_budget_period(profile)
        return budget_period['start'], budget_period['end']
    return today.replace(day=1), today
