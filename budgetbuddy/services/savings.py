"""Savings ledger — manual deposits and pay-period remainder rollover."""

from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from budgetbuddy.models import SavingsDeposit, Transaction
from budgetbuddy.services.budget_period import get_budget_period
from budgetbuddy.services.transfers import MIN_TRANSFER_AMOUNT

MIN_SAVINGS_AMOUNT = MIN_TRANSFER_AMOUNT


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


def _period_remainder(profile, period):
    manual = _manual_savings_in_period(profile, period)
    period_income = Decimal(str(profile.income_amount or 0))
    spent = _spent_in_period(profile, period)
    return max(period_income - spent - manual, Decimal('0'))


def _closed_period_starts(profile):
    return set(
        profile.savings_deposits.filter(
            source=SavingsDeposit.PERIOD_END,
        ).values_list('period_start', flat=True)
    )


def ensure_periods_closed(profile, *, on_date=None):
    """Move leftover balance into savings when a pay period has ended."""
    if on_date is None and getattr(profile, '_savings_periods_closed', False):
        return
    if on_date is None:
        profile._savings_periods_closed = True

    today = on_date or date.today()
    current = get_budget_period(profile, on_date=today)
    closed_starts = _closed_period_starts(profile)
    check_date = current['start'] - timedelta(days=1)
    anchor = profile.created_at.date()
    pending = []

    while check_date >= anchor:
        period = get_budget_period(profile, on_date=check_date)
        if period['end'] >= today:
            check_date = period['start'] - timedelta(days=1)
            continue

        if period['start'] not in closed_starts:
            remainder = _period_remainder(profile, period)
            pending.append(SavingsDeposit(
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
            ))
            closed_starts.add(period['start'])

        check_date = period['start'] - timedelta(days=1)

    if pending:
        SavingsDeposit.objects.bulk_create(pending)


def get_spendable_balance(profile):
    """Income minus spending minus manual savings moved out this period."""
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

    ensure_periods_closed(profile)
    balance = get_spendable_balance(profile)
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
    return deposit
