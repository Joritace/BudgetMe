"""Template context processors for BudgetMe."""

from django.conf import settings


def auth_providers(request):
    return {
        'google_oauth_configured': getattr(settings, 'GOOGLE_OAUTH_CONFIGURED', False),
    }
