"""Uganda-specific defaults for BudgetMe."""

CURRENCY_CODE = 'UGX'
CURRENCY_LABEL = 'Ugandan Shillings'
UGX_AMOUNT_STEP = 1000

INCOME_FREQUENCY_CHOICES = [
    ('daily', 'Daily'),
    ('biweekly', 'Bi-weekly'),
    ('monthly', 'Monthly'),
]

SUGGESTED_BUDGET_CATEGORIES = {
    'Rent': 800_000,
    'Food & Market': 450_000,
    'Transport': 200_000,
    'Utilities': 150_000,
    'Airtime & Data': 80_000,
    'School Fees': 300_000,
    'Savings (SACCO)': 400_000,
    'Health': 120_000,
    'Entertainment': 100_000,
}

DEFAULT_BUDGET_CATEGORIES = SUGGESTED_BUDGET_CATEGORIES

MOBILE_MONEY_PROVIDERS = {
    'mtn': 'MTN Mobile Money',
    'airtel': 'Airtel Money',
}

DEFAULT_PHONE_PREFIX = '+256'

CATEGORY_TO_ICON_KEY = {
    'Salary': 'salary',
    'Mobile Money': 'mobile_money',
    'Rent': 'rent',
    'Food & Market': 'food',
    'Transport': 'transport',
    'Airtime & Data': 'airtime',
    'School Fees': 'school',
    'Utilities': 'default',
    'Savings (SACCO)': 'default',
    'Health': 'default',
    'Entertainment': 'default',
}

TRANSACTION_ICON_CLASSES = {
    'salary': 'bx-wallet',
    'mobile_money': 'bx-mobile-alt',
    'rent': 'bx-home-heart',
    'food': 'bx-bowl-hot',
    'transport': 'bx-bus',
    'airtime': 'bx-wifi',
    'school': 'bx-book-reader',
    'default': 'bx-receipt',
}

CATEGORY_ICON_CLASSES = {
    'Rent': 'bx-home',
    'Food & Market': 'bx-store-alt',
    'Transport': 'bx-car',
    'Utilities': 'bx-bulb',
    'Airtime & Data': 'bx-mobile',
    'School Fees': 'bx-book-open',
    'Savings (SACCO)': 'bx-piggy-bank',
    'Health': 'bx-plus-medical',
    'Entertainment': 'bx-party',
    'default': 'bx-category-alt',
}

NAV_ITEMS = [
    {'id': 'home', 'label': 'Home', 'icon': 'bx-home-alt', 'url_name': 'dashboard'},
    {'id': 'transfer', 'label': 'Transfer', 'icon': 'bx-transfer-alt', 'url_name': 'transfer'},
    {'id': 'budget', 'label': 'Budget', 'icon': 'bx-wallet', 'url_name': 'budget_setup'},
    {'id': 'profile', 'label': 'Profile', 'icon': 'bx-user-circle', 'url_name': 'profile'},
]


def nav_items_for(active_id):
    items = []
    for item in NAV_ITEMS:
        entry = dict(item)
        entry['active'] = entry.get('id') == active_id
        items.append(entry)
    return items
