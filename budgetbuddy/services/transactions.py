"""Load and format transactions from the database."""

from budgetbuddy.constants import CATEGORY_TO_ICON_KEY
from budgetbuddy.models import Transaction


def resolve_icon_key(category, label=''):
    return CATEGORY_TO_ICON_KEY.get(category) or CATEGORY_TO_ICON_KEY.get(label, 'default')


def transaction_to_dict(transaction):
    return {
        'type': transaction.txn_type,
        'label': transaction.label,
        'category': transaction.category,
        'amount': float(transaction.amount),
        'datetime': transaction.occurred_at,
        'icon': resolve_icon_key(transaction.category, transaction.label),
    }


def get_transactions_for_profile(profile):
    return [
        transaction_to_dict(txn)
        for txn in profile.transactions.all()
    ]


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
