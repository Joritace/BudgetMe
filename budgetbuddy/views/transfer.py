"""Transfer view."""

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from budgetbuddy.constants import nav_items_for
from budgetbuddy.forms import TransferForm
from budgetbuddy.services.page_context import build_guest_context
from budgetbuddy.services.profile import get_active_profile, profile_to_user_dict
from budgetbuddy.services.transfers import create_transfer, get_available_balance, get_transfers_for_profile


@require_http_methods(['GET', 'POST'])
def transfer_home(request):
    profile = get_active_profile(request)

    if not profile:
        return render(request, 'budgetbuddy/transfer.html', build_guest_context('transfer'))

    available_balance = get_available_balance(profile)
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
                messages.success(
                    request,
                    f'{action} of UGX {mm_txn.amount:,.0f} recorded. Ref: {mm_txn.transaction_id}',
                )
                return redirect('transfer')
            except ValueError as exc:
                form.add_error(None, str(exc))
    else:
        form = TransferForm(profile, available_balance=available_balance)

    profile_name = profile.name or 'Guest'

    return render(request, 'budgetbuddy/transfer.html', {
        'has_budget': True,
        'form': form,
        'profile': profile,
        'user': user,
        'first_name': profile_name.split()[0],
        'data': {'currency': profile.currency},
        'available_balance': float(available_balance),
        'transfers': get_transfers_for_profile(profile),
        'nav_items': nav_items_for('transfer'),
        'profile_phones': {
            'mtn': profile.mtn_phone or '',
            'airtel': profile.airtel_phone or '',
        },
    })
