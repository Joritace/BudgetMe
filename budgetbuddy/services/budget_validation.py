"""Validate that budget allocations fit within income."""

from decimal import Decimal

from budgetbuddy.models import BudgetProfile


def monthly_income_from(income_amount, income_frequency):
    profile = BudgetProfile(
        income_amount=income_amount or 0,
        income_frequency=income_frequency or 'monthly',
    )
    return profile.normalized_monthly_income()


def categories_total_from_formset(formset):
    total = Decimal('0')
    for form in formset.forms:
        if not form.cleaned_data or form.cleaned_data.get('DELETE'):
            continue
        name = (form.cleaned_data.get('name') or '').strip()
        amount = form.cleaned_data.get('allocated_amount')
        if name and amount is not None:
            total += Decimal(amount)
    return total


def validate_budget_within_income(income_amount, income_frequency, saving_goal_amount, formset):
    monthly = monthly_income_from(income_amount, income_frequency)
    categories_total = categories_total_from_formset(formset)
    savings = Decimal(saving_goal_amount or 0)
    planned_total = categories_total + savings

    return planned_total <= monthly, monthly, planned_total, categories_total, savings
