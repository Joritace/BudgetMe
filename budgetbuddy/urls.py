from django.urls import path
from .views.dashboard import dashboard_home

urlpatterns = [
    path('', dashboard_home, name='dashboard'),
]