from datetime import date, timedelta

from allauth.account.views import LoginView
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from budgetbuddy.constants import nav_items_for
from budgetbuddy.services.budget_period import default_transaction_period, get_budget_period
from budgetbuddy.services.period_filter import transaction_window
from budgetbuddy.services import (
    build_dashboard_context,
    build_empty_dashboard_context,
    get_active_profile,
    get_expenses_for_profile,
    get_transactions_for_profile,
    profile_to_user_dict,
)


@require_http_methods(['GET', 'POST'])
def dashboard_home(request):
    if not request.user.is_authenticated:
        return LoginView.as_view(template_name='account/login.html')(request)

    profile = get_active_profile(request)

    if not profile:
        context = build_empty_dashboard_context(request)
        context['nav_items'] = nav_items_for('home')
        return render(request, 'budgetbuddy/dashboard.html', context)

    period = request.GET.get(
        'period',
        default_transaction_period(profile.income_frequency),
    )
    budget_period = get_budget_period(profile)
    user = profile_to_user_dict(profile)
    expenses = get_expenses_for_profile(profile, budget_period=budget_period)
    start_date, end_date = transaction_window(profile, period)
    transactions = get_transactions_for_profile(
        profile,
        start_date=start_date,
        end_date=end_date,
        limit=40,
    )

    context = build_dashboard_context(
        user, expenses, transactions,
        period=period,
        profile=profile,
    )
    context['nav_items'] = nav_items_for('home')
    context['is_authenticated'] = request.user.is_authenticated
    context['transactions_partial_url'] = reverse('api_transactions')

    return render(request, 'budgetbuddy/dashboard.html', context)
