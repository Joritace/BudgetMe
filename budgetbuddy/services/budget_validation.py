"""Validate that budget allocations fit within income per pay period."""

from decimal import Decimal


def period_income_from(income_amount, income_frequency):
    """Income cap for one budget period (not normalized to monthly)."""
    del income_frequency  # frequency selects the window, not the cap amount
    return Decimal(income_amount or 0)


def monthly_income_from(income_amount, income_frequency):
    """Backward-compatible alias used by older call sites."""
    return period_income_from(income_amount, income_frequency)


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
    period_income = period_income_from(income_amount, income_frequency)
    categories_total = categories_total_from_formset(formset)
    savings = Decimal(saving_goal_amount or 0)
    planned_total = categories_total + savings

    return planned_total <= period_income, period_income, planned_total, categories_total, savings
