"""Load and format budget profiles from the database."""

from budgetbuddy.models import BudgetProfile
from budgetbuddy.services.budget_period import get_budget_period
from budgetbuddy.services.transactions import (
    expenses_from_transactions,
    get_period_expenses_from_db,
    get_transactions_for_profile,
)


def get_active_profile(request=None, profile_id=None):
    """Return the budget profile owned by the signed-in user."""
    if request is not None:
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            cached = getattr(request, '_budget_profile', None)
            if cached is not None:
                return cached
            profile = (
                BudgetProfile.objects.filter(user=user)
                .prefetch_related('categories')
                .first()
            )
            request._budget_profile = profile
            return profile

    if profile_id:
        return (
            BudgetProfile.objects.filter(pk=profile_id)
            .prefetch_related('categories')
            .first()
        )
    return None


def profile_to_user_dict(profile):
    categories = {
        cat.name: float(cat.allocated_amount)
        for cat in profile.categories.all()
    }
    budget_period = get_budget_period(profile)
    period_income = float(profile.income_amount or 0)
    saving_goal = float(profile.saving_goal_amount) if profile.has_saving_goal else None

    return {
        'id': profile.pk,
        'name': profile.name,
        'period_income': period_income,
        'income_amount': float(profile.income_amount),
        'income_frequency': profile.income_frequency,
        'income_frequency_label': profile.income_frequency_label,
        'saving_goal_amount': saving_goal,
        'currency': profile.currency,
        'budget_categories': categories,
        'budget_period': budget_period,
    }


def get_expenses_for_profile(profile, year=None, month=None, *, budget_period=None):
    if year and month:
        transactions = get_transactions_for_profile(profile)
        expenses = expenses_from_transactions(transactions)
        return [
            expense for expense in expenses
            if expense['date'].year == year and expense['date'].month == month
        ]

    if budget_period is None:
        budget_period = get_budget_period(profile)
    return get_period_expenses_from_db(profile, budget_period)


def savings_progress(profile, expenses):
    if not profile.has_saving_goal:
        return 0

    saved = 0
    for expense in expenses:
        category = expense.get('category', '')
        if 'saving' in category.lower() or 'sacco' in category.lower():
            saved += float(expense.get('amount', 0))
    return round(saved)


def default_profile_name(user):
    full_name = user.get_full_name().strip()
    if full_name:
        return full_name
    if user.first_name:
        return user.first_name
    if user.email:
        return user.email.split('@')[0]
    return 'Friend'
