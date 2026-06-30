from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from budgetbuddy.constants import nav_items_for
from budgetbuddy.mocks import get_mock_mobile_money
from budgetbuddy.services import (
    build_dashboard_context,
    build_empty_dashboard_context,
    get_active_profile,
    get_expenses_for_profile,
    get_transactions_for_profile,
    profile_to_user_dict,
)


@require_http_methods(['GET'])
def dashboard_home(request):
    profile = get_active_profile(request)

    if not profile:
        context = build_empty_dashboard_context(request)
        context['nav_items'] = nav_items_for('home')
        return render(request, 'budgetbuddy/dashboard.html', context)

    period = request.GET.get('period', 'monthly')
    user = profile_to_user_dict(profile)
    transactions = get_transactions_for_profile(profile)
    expenses = get_expenses_for_profile(profile)
    mobile_money = get_mock_mobile_money(profile.pk)

    context = build_dashboard_context(
        user, expenses, transactions,
        period=period,
        mobile_money=mobile_money,
        profile=profile,
    )
    context['nav_items'] = nav_items_for('home')
    context['is_authenticated'] = request.user.is_authenticated

    return render(request, 'budgetbuddy/dashboard.html', context)
