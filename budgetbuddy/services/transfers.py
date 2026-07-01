"""Mobile money and cash movement processing."""

import re
import uuid
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from budgetbuddy.models import MobileMoneyTransaction, Transaction

UG_PHONE_PATTERN = re.compile(r'^(\+?256|0)?(7\d{8})$')
MIN_TRANSFER_AMOUNT = Decimal('500')

REF_PREFIX = {
    ('withdraw', 'cash'): 'CS',
    ('withdraw', 'mtn'): 'MM',
    ('withdraw', 'airtel'): 'MM',
    ('deposit', 'cash'): 'CD',
    ('deposit', 'mtn'): 'MD',
    ('deposit', 'airtel'): 'MD',
}


def normalize_phone(raw):
    cleaned = (raw or '').strip().replace(' ', '').replace('-', '')
    match = UG_PHONE_PATTERN.match(cleaned)
    if not match:
        return None
    return f'+256{match.group(2)}'


def phone_for_provider(profile, provider):
    if provider == 'mtn':
        raw = profile.mtn_phone
    elif provider == 'airtel':
        raw = profile.airtel_phone
    else:
        return ''
    if not raw:
        return ''
    return normalize_phone(raw) or raw


def generate_transaction_id(prefix='MM'):
    ts = timezone.now().strftime('%Y%m%d%H%M%S')
    return f'{prefix}{ts}{uuid.uuid4().hex[:6].upper()}'


def get_available_balance(profile):
    from budgetbuddy.services.savings import get_spendable_balance
    return get_spendable_balance(profile)


def transfer_to_dict(transfer):
    is_deposit = transfer.direction == 'deposit'
    return {
        'provider': transfer.get_provider_display(),
        'provider_key': transfer.provider,
        'direction': transfer.direction,
        'direction_label': transfer.get_direction_display(),
        'is_deposit': is_deposit,
        'transaction_id': transfer.transaction_id,
        'phone_number': transfer.phone_number,
        'is_cash': transfer.provider == 'cash',
        'amount': float(transfer.amount),
        'currency': transfer.currency,
        'status': transfer.status,
        'status_label': transfer.get_status_display(),
        'timestamp': transfer.timestamp,
    }


def get_transfers_for_profile(profile, limit=20, *, start_date=None, end_date=None):
    qs = profile.mobile_money_transactions.order_by('-timestamp')
    if start_date is not None:
        qs = qs.filter(timestamp__date__gte=start_date)
    if end_date is not None:
        qs = qs.filter(timestamp__date__lte=end_date)
    if limit is not None:
        qs = qs[:limit]
    return [transfer_to_dict(txn) for txn in qs]


def _build_label(direction, provider):
    is_withdraw = direction == 'withdraw'
    is_cash = provider == 'cash'

    if is_withdraw and is_cash:
        return 'Cash spend'
    if is_withdraw:
        return 'Mobile money spend'
    if is_cash:
        return 'Cash deposit'
    return 'Mobile money deposit'


@transaction.atomic
def create_transfer(profile, direction, provider, amount, category, phone_number='', note=''):
    amount = Decimal(amount)
    if amount < MIN_TRANSFER_AMOUNT:
        raise ValueError(f'Minimum amount is UGX {MIN_TRANSFER_AMOUNT:,.0f}')

    category_names = set(profile.categories.values_list('name', flat=True))
    if category not in category_names:
        raise ValueError('Invalid budget category')

    is_withdraw = direction == 'withdraw'
    is_cash = provider == 'cash'

    if is_withdraw:
        balance = get_available_balance(profile)
        if amount > balance:
            raise ValueError(f'Insufficient balance. Available: UGX {balance:,.0f}')

    if is_cash:
        normalized = ''
    else:
        normalized = normalize_phone(phone_number)
        if not normalized:
            raise ValueError('Invalid phone number')

    ref_prefix = REF_PREFIX.get((direction, provider), 'MM')

    mm_txn = MobileMoneyTransaction.objects.create(
        profile=profile,
        provider=provider,
        direction=direction,
        transaction_id=generate_transaction_id(ref_prefix),
        phone_number=normalized,
        amount=amount,
        currency=profile.currency,
        status='completed',
    )

    label = _build_label(direction, provider)
    note_parts = [mm_txn.get_provider_display(), mm_txn.get_direction_display()]
    if normalized:
        note_parts.append(normalized)
    if note:
        note_parts.append(note.strip())

    budget_txn = Transaction.objects.create(
        profile=profile,
        txn_type=Transaction.EXPENSE if is_withdraw else Transaction.INCOME,
        label=label,
        category=category,
        amount=amount,
        occurred_at=timezone.now(),
        note=' · '.join(note_parts),
    )

    return mm_txn, budget_txn
