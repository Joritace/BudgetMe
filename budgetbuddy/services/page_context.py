"""Shared page context for views and templates."""

from budgetbuddy.constants import nav_items_for


def build_guest_context(nav_key, *, greeting=None, user=None):
    """Context when no budget profile exists (guest / empty state)."""
    first_name = 'Friend'
    display_name = 'Guest'
    is_authenticated = False

    if user is not None and user.is_authenticated:
        is_authenticated = True
        from budgetbuddy.services.profile import default_profile_name
        display_name = default_profile_name(user)
        first_name = display_name.split()[0]

    ctx = {
        'has_budget': False,
        'is_authenticated': is_authenticated,
        'first_name': first_name,
        'user': {'name': display_name},
        'data': {'currency': 'UGX'},
        'nav_items': nav_items_for(nav_key),
    }
    if greeting is not None:
        ctx['greeting'] = greeting
    return ctx
