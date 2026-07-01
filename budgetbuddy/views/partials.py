"""JSON partials for in-page updates without full reload."""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET

from budgetbuddy.services.budget_period import default_transaction_period, period_choices_for_frequency
from budgetbuddy.services.period_filter import transaction_window
from budgetbuddy.services.profile import get_active_profile
from budgetbuddy.services.transactions import get_transactions_for_profile
from budgetbuddy.services.transfers import get_transfers_for_profile


def _period_label(profile, period):
    choices = period_choices_for_frequency(profile.income_frequency)
    return choices.get(period, period)


@login_required
@require_GET
def dashboard_transactions_partial(request):
    profile = get_active_profile(request)
    if not profile:
        return JsonResponse({'error': 'No budget profile'}, status=404)

    allowed = period_choices_for_frequency(profile.income_frequency)
    period = request.GET.get('period', default_transaction_period(profile.income_frequency))
    if period not in allowed:
        period = default_transaction_period(profile.income_frequency)

    start_date, end_date = transaction_window(profile, period)
    transactions = get_transactions_for_profile(
        profile,
        start_date=start_date,
        end_date=end_date,
        limit=40,
    )
    html = render_to_string(
        'budgetbuddy/partials/dash_transactions.html',
        {
            'transactions': transactions,
            'currency': profile.currency,
        },
        request=request,
    )
    return JsonResponse({
        'html': html,
        'period': period,
        'label': _period_label(profile, period),
    })


@login_required
@require_GET
def transfer_movements_partial(request):
    profile = get_active_profile(request)
    if not profile:
        return JsonResponse({'error': 'No budget profile'}, status=404)

    allowed = period_choices_for_frequency(profile.income_frequency)
    period = request.GET.get('period', default_transaction_period(profile.income_frequency))
    if period not in allowed:
        period = default_transaction_period(profile.income_frequency)

    start_date, end_date = transaction_window(profile, period)
    transfers = get_transfers_for_profile(
        profile,
        limit=30,
        start_date=start_date,
        end_date=end_date,
    )
    html = render_to_string(
        'budgetbuddy/partials/transfer_movements.html',
        {'transfers': transfers},
        request=request,
    )
    return JsonResponse({
        'html': html,
        'period': period,
        'label': _period_label(profile, period),
    })
