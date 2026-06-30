"""Template context processors for BudgetMe."""

from budgetbuddy.services.google_oauth import is_google_oauth_configured


def auth_providers(request):
    return {
        'google_oauth_configured': is_google_oauth_configured(),
    }
