"""Savings ledger — manual deposits and pay-period remainder rollover."""

from datetime import date, timedelta
from decimal import Decimal

from django.core.cache import cache
from django.db import transaction
from django.db.models import Sum

from budgetbuddy.models import SavingsDeposit, Transaction
from budgetbuddy.services.budget_period import get_budget_period
from budgetbuddy.services.transfers import MIN_TRANSFER_AMOUNT

MIN_SAVINGS_AMOUNT = MIN_TRANSFER_AMOUNT
MAX_PERIODS_CLOSE_PER_REQUEST = 1
_PERIOD_CLOSE_CACHE_SECONDS = 60 * 30


def deposit_to_dict(deposit):
    return {
        'id': deposit.pk,
        'amount': float(deposit.amount),
        'source': deposit.source,
        'source_label': deposit.source_label,
        'note': deposit.note,
        'period_start': deposit.period_start,
        'period_end': deposit.period_end,
        'created_at': deposit.created_at,
        'is_manual': deposit.source == SavingsDeposit.MANUAL,
        'is_period_end': deposit.source == SavingsDeposit.PERIOD_END,
    }


def get_savings_deposits_for_profile(profile, limit=None):
    qs = profile.savings_deposits.filter(amount__gt=0)
    if limit is not None:
        qs = qs[:limit]
    return [deposit_to_dict(deposit) for deposit in qs]


def get_total_savings(profile):
    total = profile.savings_deposits.aggregate(total=Sum('amount'))['total']
    return float(total or 0)


def _manual_savings_in_period(profile, period):
    start = period['start']
    end = period['end']
    total = profile.savings_deposits.filter(
        source=SavingsDeposit.MANUAL,
        created_at__date__gte=start,
        created_at__date__lte=end,
    ).aggregate(total=Sum('amount'))['total']
    return Decimal(str(total or 0))


def savings_in_period(profile, period):
    """All savings credited during a budget window (manual + period-end for that window)."""
    manual = _manual_savings_in_period(profile, period)
    period_end = profile.savings_deposits.filter(
        source=SavingsDeposit.PERIOD_END,
        period_start=period['start'],
    ).aggregate(total=Sum('amount'))['total']
    return float(manual + Decimal(str(period_end or 0)))


def _spent_in_period(profile, period):
    total = Transaction.objects.filter(
        profile=profile,
        txn_type=Transaction.EXPENSE,
        occurred_at__date__gte=period['start'],
        occurred_at__date__lte=period['end'],
    ).aggregate(total=Sum('amount'))['total']
    return Decimal(str(total or 0))


def _period_close_cache_key(profile):
    return f'bb:period-close:{profile.pk}:{date.today().isoformat()}'


MAX_PERIOD_SCAN = 120


def _next_unclosed_period(profile, today, current):
    """Return at most one ended period that still needs closing."""
    last_check = current['start'] - timedelta(days=1)
    walk_start = profile.created_at.date()
    if walk_start > last_check:
        return None

    closed_starts = set(
        profile.savings_deposits.filter(source=SavingsDeposit.PERIOD_END)
        .values_list('period_start', flat=True)
    )

    day = walk_start
    scanned = 0
    while day <= last_check and scanned < MAX_PERIOD_SCAN:
        scanned += 1
        period = get_budget_period(profile, on_date=day)
        if period['end'] >= today:
            return None
        if period['start'] not in closed_starts:
            return period
        day = period['end'] + timedelta(days=1)
    return None


def ensure_periods_closed(profile, *, on_date=None, force=False):
    """Close at most one ended pay period per request (fast path for navigation)."""
    if on_date is None:
        if getattr(profile, '_savings_periods_closed', False):
            return
        profile._savings_periods_closed = True
        if not force and cache.get(_period_close_cache_key(profile)):
            return

    today = on_date or date.today()
    current = get_budget_period(profile, on_date=today)
    period = _next_unclosed_period(profile, today, current)
    if period is None:
        if on_date is None:
            cache.set(_period_close_cache_key(profile), True, _PERIOD_CLOSE_CACHE_SECONDS)
        return

    spent = _spent_in_period(profile, period)
    manual = _manual_savings_in_period(profile, period)
    period_income = Decimal(str(profile.income_amount or 0))
    remainder = max(period_income - spent - manual, Decimal('0'))
    SavingsDeposit.objects.create(
        profile=profile,
        amount=remainder,
        source=SavingsDeposit.PERIOD_END,
        period_start=period['start'],
        period_end=period['end'],
        note=(
            f'Leftover from {period["label"]}'
            if remainder > 0
            else f'No leftover from {period["label"]}'
        ),
    )
    if on_date is None:
        cache.set(_period_close_cache_key(profile), True, _PERIOD_CLOSE_CACHE_SECONDS)


def get_spendable_balance(profile, *, close_periods=True):
    """Income minus spending minus manual savings moved out this period."""
    if close_periods:
        ensure_periods_closed(profile)
    budget_period = get_budget_period(profile)
    manual = _manual_savings_in_period(profile, budget_period)
    period_income = Decimal(str(profile.income_amount or 0))
    spent = _spent_in_period(profile, budget_period)
    return max(period_income - spent - manual, Decimal('0'))


@transaction.atomic
def create_manual_savings_deposit(profile, amount, note=''):
    amount = Decimal(amount)
    if amount < MIN_SAVINGS_AMOUNT:
        raise ValueError(f'Minimum savings amount is UGX {MIN_SAVINGS_AMOUNT:,.0f}')

    ensure_periods_closed(profile, force=True)
    balance = get_spendable_balance(profile, close_periods=False)
    if amount > balance:
        raise ValueError(f'Insufficient balance. Available: UGX {balance:,.0f}')

    budget_period = get_budget_period(profile)
    deposit = SavingsDeposit.objects.create(
        profile=profile,
        amount=amount,
        source=SavingsDeposit.MANUAL,
        period_start=budget_period['start'],
        period_end=budget_period['end'],
        note=note.strip(),
    )
    cache.delete(_period_close_cache_key(profile))
    return deposit
