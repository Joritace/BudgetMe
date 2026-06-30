"""Google OAuth configuration helpers."""

from django.conf import settings


def is_google_oauth_configured():
    """True when a Google SocialApp exists for the current site."""
    try:
        from allauth.socialaccount.models import SocialApp
        from django.contrib.sites.models import Site

        site = Site.objects.get_current()
        return SocialApp.objects.filter(provider='google', sites=site).exists()
    except Exception:
        return getattr(settings, 'GOOGLE_OAUTH_CONFIGURED', False)
