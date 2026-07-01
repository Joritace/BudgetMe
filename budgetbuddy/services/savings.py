"""Savings ledger — manual deposits and pay-period remainder rollover."""

from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

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


def _closed_period_starts(profile):
    return set(
        profile.savings_deposits.filter(
            source=SavingsDeposit.PERIOD_END,
        ).values_list('period_start', flat=True)
    )


def _pending_ended_periods(profile, today, current, closed_starts):
    """Ended pay periods that still need closing, walking forward from the last close."""
    latest_closed_start = (
        profile.savings_deposits.filter(source=SavingsDeposit.PERIOD_END)
        .order_by('-period_start')
        .values_list('period_start', flat=True)
        .first()
    )
    if latest_closed_start:
        last_closed = get_budget_period(profile, on_date=latest_closed_start)
        walk_start = last_closed['end'] + timedelta(days=1)
    else:
        walk_start = profile.created_at.date()

    pending = []
    day = walk_start
    last_check = current['start'] - timedelta(days=1)
    while day <= last_check:
        period = get_budget_period(profile, on_date=day)
        if period['end'] >= today:
            break
        if period['start'] not in closed_starts:
            pending.append(period)
            closed_starts.add(period['start'])
        day = period['end'] + timedelta(days=1)
    return pending


def ensure_periods_closed(profile, *, on_date=None):
    """Move leftover balance into savings when a pay period has ended."""
    if on_date is None and getattr(profile, '_savings_periods_closed', False):
        return
    if on_date is None:
        profile._savings_periods_closed = True

    today = on_date or date.today()
    current = get_budget_period(profile, on_date=today)
    closed_starts = _closed_period_starts(profile)
    pending_periods = _pending_ended_periods(profile, today, current, closed_starts)
    if not pending_periods:
        return

    min_start = min(period['start'] for period in pending_periods)
    max_end = max(period['end'] for period in pending_periods)
    period_income = Decimal(str(profile.income_amount or 0))

    expense_rows = list(
        Transaction.objects.filter(
            profile=profile,
            txn_type=Transaction.EXPENSE,
            occurred_at__date__gte=min_start,
            occurred_at__date__lte=max_end,
        ).values_list('amount', 'occurred_at')
    )
    manual_rows = list(
        profile.savings_deposits.filter(
            source=SavingsDeposit.MANUAL,
            created_at__date__gte=min_start,
            created_at__date__lte=max_end,
        ).values_list('amount', 'created_at')
    )

    to_create = []
    for period in pending_periods:
        start = period['start']
        end = period['end']
        spent = sum(
            Decimal(str(amount))
            for amount, occurred_at in expense_rows
            if start <= occurred_at.date() <= end
        )
        manual = sum(
            Decimal(str(amount))
            for amount, created_at in manual_rows
            if start <= created_at.date() <= end
        )
        remainder = max(period_income - spent - manual, Decimal('0'))
        to_create.append(SavingsDeposit(
            profile=profile,
            amount=remainder,
            source=SavingsDeposit.PERIOD_END,
            period_start=start,
            period_end=end,
            note=(
                f'Leftover from {period["label"]}'
                if remainder > 0
                else f'No leftover from {period["label"]}'
            ),
        ))

    SavingsDeposit.objects.bulk_create(to_create)


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
