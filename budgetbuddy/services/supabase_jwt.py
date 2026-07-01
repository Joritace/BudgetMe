"""Short-lived JWTs for Supabase Realtime (Django session → RLS)."""

from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings


def create_supabase_realtime_token(user):
    """Sign a JWT Supabase Realtime accepts for RLS policies using django_user_id."""
    now = datetime.now(timezone.utc)
    payload = {
        'role': 'authenticated',
        'aud': 'authenticated',
        'sub': str(user.pk),
        'django_user_id': user.pk,
        'iat': int(now.timestamp()),
        'exp': int((now + timedelta(hours=1)).timestamp()),
    }
    return jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm='HS256')
