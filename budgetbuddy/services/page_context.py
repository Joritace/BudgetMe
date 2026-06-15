"""Shared page context for views and templates."""

from budgetbuddy.constants import nav_items_for


def build_guest_context(nav_key, *, greeting=None):
    """Context when no budget profile exists (guest / empty state)."""
    ctx = {
        'has_budget': False,
        'first_name': 'Friend',
        'user': {'name': 'Guest'},
        'data': {'currency': 'UGX'},
        'nav_items': nav_items_for(nav_key),
    }
    if greeting is not None:
        ctx['greeting'] = greeting
    return ctx
