"""Template context processors for BudgetMe."""

from django.conf import settings
from django.urls import reverse


def auth_providers(request):
    return {
        'google_oauth_configured': getattr(settings, 'GOOGLE_OAUTH_CONFIGURED', False),
    }


def supabase_realtime(request):
    """Expose Supabase client config for logged-in users with a budget profile."""
    if not getattr(settings, 'SUPABASE_REALTIME_ENABLED', False):
        return {'supabase_realtime': None}

    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {'supabase_realtime': None}

    from budgetbuddy.services.profile import get_active_profile

    profile = get_active_profile(request)
    if not profile:
        return {'supabase_realtime': None}

    return {
        'supabase_realtime': {
            'url': settings.SUPABASE_URL,
            'anonKey': settings.SUPABASE_ANON_KEY,
            'profileId': profile.pk,
            'tokenUrl': reverse('api_supabase_realtime_token'),
            'summaryUrl': reverse('api_live_summary'),
        },
    }
