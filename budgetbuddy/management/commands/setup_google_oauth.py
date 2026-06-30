"""Sync Google OAuth credentials from environment into django-allauth."""

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand

from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = 'Create or update the Google SocialApp from GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET.'

    def handle(self, *args, **options):
        client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '').strip()
        secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', '').strip()
        callback_uri = getattr(settings, 'GOOGLE_OAUTH_CALLBACK_URI', '').strip()

        if not client_id or not secret:
            self.stderr.write(
                self.style.ERROR(
                    'Missing credentials. Add these to a .env file in the project root:\n'
                    '  GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com\n'
                    '  GOOGLE_CLIENT_SECRET=your-client-secret\n\n'
                    'Get them from Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client.'
                )
            )
            return

        site = Site.objects.get_current()

        google_apps = list(SocialApp.objects.filter(provider='google').order_by('pk'))
        if len(google_apps) > 1:
            keep_pk = google_apps[0].pk
            SocialApp.objects.filter(provider='google').exclude(pk=keep_pk).delete()
            self.stdout.write(self.style.WARNING(f'Removed {len(google_apps) - 1} duplicate Google app(s).'))

        app, created = SocialApp.objects.update_or_create(
            provider='google',
            defaults={
                'name': 'Google',
                'client_id': client_id,
                'secret': secret,
            },
        )
        app.sites.set([site])

        action = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{action} Google OAuth app for site "{site.domain}".'))
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Add this EXACT redirect URI in Google Cloud Console:'))
        self.stdout.write(f'  → Credentials → your OAuth client → Authorized redirect URIs')
        self.stdout.write(self.style.NOTICE(f'  {callback_uri or "(set GOOGLE_OAUTH_CALLBACK_URI in .env)"}'))
        self.stdout.write('')
        self.stdout.write('Use http://127.0.0.1:8000/ in your browser (not localhost).')
        self.stdout.write('Restart the dev server after saving Google Console changes.')
