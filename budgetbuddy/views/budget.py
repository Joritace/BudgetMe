"""Budget setup view."""

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from budgetbuddy.constants import nav_items_for
from budgetbuddy.forms import BudgetCategoryFormSet, BudgetProfileForm, suggested_category_initial
from budgetbuddy.models import BudgetCategory, BudgetProfile
from budgetbuddy.services.budget_validation import monthly_income_from, validate_budget_within_income
from budgetbuddy.services.profile import clear_active_profile, get_active_profile, set_active_profile


def _save_categories(formset, profile):
    instances = formset.save(commit=False)
    for category in instances:
        if not category.name:
            continue
        category.profile = profile
        category.save()
    for obj in formset.deleted_objects:
        obj.delete()


@require_http_methods(['GET', 'POST'])
def budget_setup(request):
    profile = get_active_profile(request)
    is_new = profile is None

    if request.method == 'POST':
        form = BudgetProfileForm(request.POST, instance=profile)
        formset = BudgetCategoryFormSet(
            request.POST,
            queryset=BudgetCategory.objects.none() if is_new else profile.categories.all(),
        )

        if form.is_valid() and formset.is_valid():
            income_amount = form.cleaned_data['income_amount']
            income_frequency = form.cleaned_data['income_frequency']
            saving_goal = form.cleaned_data.get('saving_goal_amount')

            is_valid, monthly, planned, categories_total, savings = validate_budget_within_income(
                income_amount, income_frequency, saving_goal, formset,
            )

            if not is_valid:
                form.add_error(
                    None,
                    f'Your budget total (UGX {categories_total:,.0f} categories + '
                    f'UGX {savings:,.0f} savings = UGX {planned:,.0f}) '
                    f'cannot exceed your monthly income (UGX {monthly:,.0f}). '
                    f'Reduce categories or saving goal.',
                )
            else:
                with transaction.atomic():
                    profile = form.save()
                    _save_categories(formset, profile)

                set_active_profile(request, profile)
                messages.success(request, 'Your budget has been saved.')
                return redirect('dashboard')
    else:
        if is_new:
            form = BudgetProfileForm(initial={'income_frequency': 'monthly'})
            formset = BudgetCategoryFormSet(
                queryset=BudgetCategory.objects.none(),
                initial=suggested_category_initial(),
            )
        else:
            form = BudgetProfileForm(instance=profile)
            formset = BudgetCategoryFormSet(queryset=profile.categories.all())

    profile_name = profile.name if profile and profile.name else 'Guest'
    income_preview = None
    if request.method == 'POST' and form.is_bound:
        try:
            income_preview = float(
                monthly_income_from(
                    form.data.get('income_amount'),
                    form.data.get('income_frequency', 'monthly'),
                )
            )
        except (TypeError, ValueError):
            pass
    elif profile and not is_new:
        income_preview = float(profile.normalized_monthly_income())

    return render(request, 'budgetbuddy/budget_setup.html', {
        'form': form,
        'formset': formset,
        'profile': profile,
        'is_new': is_new,
        'nav_items': nav_items_for('budget'),
        'user': {'name': profile_name},
        'first_name': profile_name.split()[0],
        'data': {'currency': 'UGX'},
        'monthly_income_preview': income_preview,
    })


@require_http_methods(['POST'])
def budget_delete(request):
    profile = get_active_profile(request)
    if not profile:
        messages.info(request, 'No budget to delete.')
        return redirect('dashboard')

    name = profile.name
    profile.delete()
    clear_active_profile(request)
    messages.success(request, f'Budget for {name} has been deleted.')
    return redirect('dashboard')
