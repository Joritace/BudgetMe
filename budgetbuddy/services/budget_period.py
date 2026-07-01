"""Budget window helpers — monthly calendar months vs bi-weekly pay periods."""

from calendar import monthrange
from datetime import date, timedelta


def get_budget_period(profile, *, on_date=None):
    """Return the active budget window for a profile's income frequency."""
    today = on_date or date.today()
    freq = profile.income_frequency
    income = float(profile.income_amount or 0)

    if freq == 'biweekly':
        anchor = profile.created_at.date()
        days_since = (today - anchor).days
        period_index = max(days_since, 0) // 14
        start = anchor + timedelta(days=period_index * 14)
        end = start + timedelta(days=13)
        label = f'{start.strftime("%b %d")} – {end.strftime("%b %d, %Y")}'
        title = 'Pay period'
        short_label = 'Pay period'
    elif freq == 'daily':
        start = today
        end = today
        label = today.strftime('%B %d, %Y')
        title = 'Today'
        short_label = 'Today'
    else:
        start = today.replace(day=1)
        last_day = monthrange(today.year, today.month)[1]
        end = today.replace(day=last_day)
        label = today.strftime('%B %Y')
        title = label
        short_label = 'Monthly'

    return {
        'start': start,
        'end': end,
        'label': label,
        'title': title,
        'short_label': short_label,
        'period_income': income,
        'frequency': freq,
        'frequency_label': profile.income_frequency_label,
        'days_in_period': (end - start).days + 1,
    }


def filter_expenses_for_period(expenses, period):
    start = period['start']
    end = period['end']
    return [
        expense for expense in expenses
        if start <= expense['date'] <= end
    ]


def default_transaction_period(income_frequency):
    if income_frequency == 'biweekly':
        return 'biweekly'
    if income_frequency == 'daily':
        return 'daily'
    return 'monthly'


def period_choices_for_frequency(income_frequency):
    if income_frequency == 'biweekly':
        return {
            'biweekly': 'Pay period',
            'weekly': 'This week',
            'daily': 'Today',
        }
    if income_frequency == 'daily':
        return {
            'daily': 'Today',
            'weekly': 'This week',
        }
    return {
        'monthly': 'This month',
        'weekly': 'This week',
        'daily': 'Today',
    }
