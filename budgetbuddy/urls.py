from django.urls import path

from .views.auth_status import auth_status
from .views.budget import budget_delete, budget_setup
from .views.dashboard import dashboard_home
from .views.profile import profile_home
from .views.partials import dashboard_transactions_partial, transfer_movements_partial
from .views.pwa import apple_touch_icon, icon_192, icon_512, service_worker, web_manifest
from .views.savings import savings_home
from .views.supabase_api import live_summary, supabase_realtime_token
from .views.transfer import transfer_home

urlpatterns = [
    path('', dashboard_home, name='dashboard'),
    path('site.webmanifest', web_manifest, name='web_manifest'),
    path('sw.js', service_worker, name='service_worker'),
    path('apple-touch-icon.png', apple_touch_icon),
    path('icon-192.png', icon_192),
    path('icon-512.png', icon_512),
    path('auth/status/', auth_status, name='auth_status'),
    path('transfer/', transfer_home, name='transfer'),
    path('savings/', savings_home, name='savings'),
    path('api/transactions/', dashboard_transactions_partial, name='api_transactions'),
    path('api/transfers/', transfer_movements_partial, name='api_transfers'),
    path('api/supabase/realtime-token/', supabase_realtime_token, name='api_supabase_realtime_token'),
    path('api/live/summary/', live_summary, name='api_live_summary'),
    path('budget/', budget_setup, name='budget_setup'),
    path('budget/delete/', budget_delete, name='budget_delete'),
    path('profile/', profile_home, name='profile'),
]
