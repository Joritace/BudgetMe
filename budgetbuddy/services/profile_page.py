"""Profile page context and helpers."""

from budgetbuddy.constants import MOBILE_MONEY_PROVIDERS
from budgetbuddy.services.budget import summarize_budget
from budgetbuddy.services.budget_period import get_budget_period
from budgetbuddy.services.profile import get_expenses_for_profile, profile_to_user_dict
from budgetbuddy.services.transfers import get_available_balance


def phone_status(profile):
    return {
        'mtn': {
            'label': MOBILE_MONEY_PROVIDERS['mtn'],
            'number': profile.mtn_phone or '',
            'configured': bool(profile.mtn_phone),
        },
        'airtel': {
            'label': MOBILE_MONEY_PROVIDERS['airtel'],
            'number': profile.airtel_phone or '',
            'configured': bool(profile.airtel_phone),
        },
        'configured_count': sum(1 for n in (profile.mtn_phone, profile.airtel_phone) if n),
    }


def build_profile_context(profile):
    user = profile_to_user_dict(profile)
    budget_period = get_budget_period(profile)
    expenses = get_expenses_for_profile(profile, budget_period=budget_period)
    summary = summarize_budget(user, expenses, period=budget_period)
    available = float(get_available_balance(profile))
    profile_name = profile.name or 'Guest'

    top_categories = sorted(
        summary['overview'],
        key=lambda row: row['spent'],
        reverse=True,
    )[:4]

    return {
        'user': user,
        'profile': profile,
        'first_name': profile_name.split()[0],
        'phone_status': phone_status(profile),
        'stats': {
            'available_balance': available,
            'total_spent': summary['total_spent'],
            'total_allocated': summary['total_allocated'],
            'transaction_count': profile.transactions.count(),
            'transfer_count': profile.mobile_money_transactions.count(),
        },
        'data': {
            'currency': profile.currency,
            'period_income': float(profile.income_amount or 0),
            'category_count': profile.categories.count(),
            'member_since': profile.created_at,
            'last_updated': profile.updated_at,
            'saving_goal': float(profile.saving_goal_amount) if profile.has_saving_goal else None,
            'income_amount': float(profile.income_amount),
            'income_frequency_label': profile.income_frequency_label,
            'budget_period_label': budget_period['label'],
        },
        'budget_snapshot': {
            'month': summary['period_label'],
            'top_categories': top_categories,
        },
        'budget_period': budget_period,
    }
