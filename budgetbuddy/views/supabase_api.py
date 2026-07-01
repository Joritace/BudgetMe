"""Supabase Realtime support — JWT minting and live summary for UI refresh."""

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET

from budgetbuddy.services.budget import summarize_budget
from budgetbuddy.services.budget_period import get_budget_period
from budgetbuddy.services.profile import get_active_profile, get_expenses_for_profile, profile_to_user_dict
from budgetbuddy.services.savings import get_savings_deposits_for_profile, get_spendable_balance, get_total_savings, savings_in_period
from budgetbuddy.services.supabase_jwt import create_supabase_realtime_token
from budgetbuddy.services.transfers import get_available_balance


def _realtime_disabled():
    return JsonResponse({'error': 'Supabase Realtime is not configured'}, status=404)


@login_required
@require_GET
def supabase_realtime_token(request):
    if not settings.SUPABASE_REALTIME_ENABLED:
        return _realtime_disabled()
    return JsonResponse({'token': create_supabase_realtime_token(request.user)})


@login_required
@require_GET
def live_summary(request):
    """Numbers + optional HTML fragments for realtime UI refresh."""
    profile = get_active_profile(request)
    if not profile:
        return JsonResponse({'error': 'No budget profile'}, status=404)

    budget_period = get_budget_period(profile)
    user = profile_to_user_dict(profile)
    expenses = get_expenses_for_profile(profile, budget_period=budget_period)
    data = summarize_budget(user, expenses, period=budget_period)
    period_income = user.get('period_income') or user.get('income_amount', 0)
    budget_used_percent = round(
        (data['total_spent'] / period_income * 100) if period_income else 0,
        1,
    )
    total_balance = float(get_spendable_balance(profile, close_periods=False))
    available_balance = float(get_available_balance(profile, close_periods=False))
    total_savings = get_total_savings(profile)
    period_savings = savings_in_period(profile, budget_period)
    saving_goal = float(profile.saving_goal_amount) if profile.has_saving_goal else None
    goal_percent = min(round((period_savings / saving_goal * 100) if saving_goal else 0), 100)

    payload = {
        'currency': profile.currency,
        'total_balance': round(total_balance),
        'total_spent': data['total_spent'],
        'budget_used_percent': min(budget_used_percent, 100),
        'available_balance': round(available_balance),
        'total_savings': round(total_savings),
        'period_savings': round(period_savings),
        'goal_percent': goal_percent,
        'saving_goal': round(saving_goal) if saving_goal else None,
        'period_label': budget_period['label'],
    }

    if request.GET.get('include') == 'deposits':
        deposits = get_savings_deposits_for_profile(profile)
        payload['deposits_html'] = render_to_string(
            'budgetbuddy/partials/savings_deposits.html',
            {'deposits': deposits, 'currency': profile.currency},
            request=request,
        )

    return JsonResponse(payload)
