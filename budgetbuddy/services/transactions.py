"""Load and format transactions from the database."""

from budgetbuddy.constants import CATEGORY_TO_ICON_KEY
from budgetbuddy.models import Transaction


def resolve_icon_key(category, label=''):
    return CATEGORY_TO_ICON_KEY.get(category) or CATEGORY_TO_ICON_KEY.get(label, 'default')


def transaction_to_dict(transaction):
    note = transaction.note or ''
    provider_key = _provider_from_note(note)
    icon = resolve_icon_key(transaction.category, transaction.label)
    if provider_key and icon == 'mobile_money':
        icon = provider_key
    return {
        'type': transaction.txn_type,
        'label': transaction.label,
        'category': transaction.category,
        'amount': float(transaction.amount),
        'datetime': transaction.occurred_at,
        'icon': icon,
        'provider_key': provider_key,
    }


def _provider_from_note(note):
    lowered = (note or '').lower()
    if 'mtn' in lowered:
        return 'mtn'
    if 'airtel' in lowered:
        return 'airtel'
    if 'cash' in lowered:
        return 'cash'
    return None


def get_transactions_for_profile(profile, *, start_date=None, end_date=None, limit=None):
    qs = profile.transactions.order_by('-occurred_at')
    if start_date is not None:
        qs = qs.filter(occurred_at__date__gte=start_date)
    if end_date is not None:
        qs = qs.filter(occurred_at__date__lte=end_date)
    if limit is not None:
        qs = qs[:limit]
    return [transaction_to_dict(txn) for txn in qs]


def expenses_from_transactions(transactions):
    return [
        {
            'date': txn['datetime'].date() if hasattr(txn['datetime'], 'date') else txn['datetime'],
            'category': txn['category'],
            'amount': txn['amount'],
        }
        for txn in transactions
        if txn['type'] == 'expense'
    ]


def get_period_expenses_from_db(profile, budget_period):
    """Load only expense rows for a budget window — avoids scanning all history."""
    rows = Transaction.objects.filter(
        profile=profile,
        txn_type=Transaction.EXPENSE,
        occurred_at__date__gte=budget_period['start'],
        occurred_at__date__lte=budget_period['end'],
    ).values('category', 'amount', 'occurred_at')
    return [
        {
            'date': row['occurred_at'].date(),
            'category': row['category'],
            'amount': float(row['amount']),
        }
        for row in rows
    ]
