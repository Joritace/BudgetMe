"""Transfer view."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from budgetbuddy.constants import nav_items_for
from budgetbuddy.forms import TransferForm
from budgetbuddy.views.http_helpers import ajax_form_errors, ajax_success, is_bb_ajax
from budgetbuddy.services.budget_period import (
    default_transaction_period,
    get_budget_period,
    period_choices_for_frequency,
)
from budgetbuddy.services.page_context import build_guest_context
from budgetbuddy.services.period_filter import transaction_window
from budgetbuddy.services.profile import get_active_profile, profile_to_user_dict
from budgetbuddy.services.transfers import create_transfer, get_available_balance, get_transfers_for_profile


@login_required
@require_http_methods(['GET', 'POST'])
def transfer_home(request):
    profile = get_active_profile(request)

    if not profile:
        return render(
            request,
            'budgetbuddy/transfer.html',
            build_guest_context('transfer', user=request.user),
        )

    close_periods = request.method == 'POST'
    available_balance = get_available_balance(profile, close_periods=close_periods)
    user = profile_to_user_dict(profile)

    if request.method == 'POST':
        form = TransferForm(profile, available_balance=available_balance, data=request.POST)
        if form.is_valid():
            try:
                mm_txn, _ = create_transfer(
                    profile=profile,
                    direction=form.cleaned_data['direction'],
                    provider=form.cleaned_data['provider'],
                    amount=form.cleaned_data['amount'],
                    category=form.cleaned_data['category'],
                    phone_number=form.cleaned_data.get('phone_number', ''),
                    note=form.cleaned_data.get('note', ''),
                )
                action = 'Spend' if mm_txn.direction == 'withdraw' else 'Deposit'
                msg = f'{action} of UGX {mm_txn.amount:,.0f} recorded. Ref: {mm_txn.transaction_id}'
                if is_bb_ajax(request):
                    return ajax_success(msg)
                messages.success(request, msg)
                return redirect('transfer')
            except ValueError as exc:
                form.add_error(None, str(exc))
        if is_bb_ajax(request):
            return ajax_form_errors(form)
    else:
        form = TransferForm(profile, available_balance=available_balance)

    profile_name = profile.name or 'Guest'
    budget_period = get_budget_period(profile)
    period = request.GET.get(
        'period',
        default_transaction_period(profile.income_frequency),
    )
    start_date, end_date = transaction_window(profile, period)
    transfers = get_transfers_for_profile(
        profile,
        limit=30,
        start_date=start_date,
        end_date=end_date,
    )

    return render(request, 'budgetbuddy/transfer.html', {
        'has_budget': True,
        'is_authenticated': True,
        'form': form,
        'profile': profile,
        'user': user,
        'first_name': profile_name.split()[0],
        'data': {'currency': profile.currency},
        'available_balance': float(available_balance),
        'transfers': transfers,
        'period': period,
        'period_choices': period_choices_for_frequency(profile.income_frequency),
        'transfers_partial_url': reverse('api_transfers'),
        'nav_items': nav_items_for('transfer'),
        'budget_period': budget_period,
        'profile_phones': {
            'mtn': profile.mtn_phone or '',
            'airtel': profile.airtel_phone or '',
        },
    })
