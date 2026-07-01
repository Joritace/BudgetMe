"""Savings view — add to savings and view savings history."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from budgetbuddy.constants import nav_items_for
from budgetbuddy.forms import SavingsDepositForm
from budgetbuddy.views.http_helpers import ajax_form_errors, ajax_success, is_bb_ajax
from budgetbuddy.services.budget_period import get_budget_period
from budgetbuddy.services.page_context import build_guest_context
from budgetbuddy.services.profile import get_active_profile, profile_to_user_dict
from budgetbuddy.services.savings import (
    create_manual_savings_deposit,
    get_savings_deposits_for_profile,
    get_total_savings,
    savings_in_period,
)
from budgetbuddy.services.transfers import get_available_balance


@login_required
@require_http_methods(['GET', 'POST'])
def savings_home(request):
    profile = get_active_profile(request)

    if not profile:
        return render(
            request,
            'budgetbuddy/savings.html',
            build_guest_context('savings', user=request.user),
        )

    close_periods = request.method == 'POST'
    available_balance = get_available_balance(profile, close_periods=close_periods)
    user = profile_to_user_dict(profile)
    budget_period = get_budget_period(profile)
    total_savings = get_total_savings(profile)
    period_savings = savings_in_period(profile, budget_period)
    saving_goal = float(profile.saving_goal_amount) if profile.has_saving_goal else None

    if request.method == 'POST':
        form = SavingsDepositForm(available_balance=available_balance, data=request.POST)
        if form.is_valid():
            try:
                deposit = create_manual_savings_deposit(
                    profile=profile,
                    amount=form.cleaned_data['amount'],
                    note=form.cleaned_data.get('note', ''),
                )
                msg = f'UGX {deposit.amount:,.0f} moved to savings.'
                if is_bb_ajax(request):
                    return ajax_success(msg)
                messages.success(request, msg)
                return redirect('savings')
            except ValueError as exc:
                form.add_error(None, str(exc))
        if is_bb_ajax(request):
            return ajax_form_errors(form)
    else:
        form = SavingsDepositForm(available_balance=available_balance)

    profile_name = profile.name or 'Guest'
    goal_percent = min(round((period_savings / saving_goal * 100) if saving_goal else 0), 100)

    return render(request, 'budgetbuddy/savings.html', {
        'has_budget': True,
        'is_authenticated': True,
        'form': form,
        'profile': profile,
        'user': user,
        'first_name': profile_name.split()[0],
        'data': {'currency': profile.currency},
        'available_balance': float(available_balance),
        'total_savings': total_savings,
        'period_savings': period_savings,
        'saving_goal': saving_goal,
        'goal_percent': goal_percent,
        'deposits': get_savings_deposits_for_profile(profile),
        'nav_items': nav_items_for('savings'),
        'budget_period': budget_period,
    })
