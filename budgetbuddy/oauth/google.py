"""Google OAuth adapter with a fixed callback URI for local development."""

from django.conf import settings
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter


class BudgetGoogleOAuth2Adapter(GoogleOAuth2Adapter):
    """Use a single canonical redirect URI so Google Cloud Console only needs one entry."""

    def get_callback_url(self, request, app):
        fixed_uri = getattr(settings, 'GOOGLE_OAUTH_CALLBACK_URI', '').strip()
        if fixed_uri:
            return fixed_uri
        return super().get_callback_url(request, app)
