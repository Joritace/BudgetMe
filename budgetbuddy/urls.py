from django.urls import path

from .views.auth_status import auth_status
from .views.budget import budget_delete, budget_setup
from .views.dashboard import dashboard_home
from .views.profile import profile_home
from .views.transfer import transfer_home

urlpatterns = [
    path('', dashboard_home, name='dashboard'),
    path('auth/status/', auth_status, name='auth_status'),
    path('transfer/', transfer_home, name='transfer'),
    path('budget/', budget_setup, name='budget_setup'),
    path('budget/delete/', budget_delete, name='budget_delete'),
    path('profile/', profile_home, name='profile'),
]
