"""
URL configuration for BudgetMe project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

from allauth.socialaccount.providers.oauth2.views import OAuth2CallbackView, OAuth2LoginView

from budgetbuddy.oauth.google import BudgetGoogleOAuth2Adapter

urlpatterns = [
    path('admin/', admin.site.urls),
    # Override Google OAuth routes so redirect_uri is always the canonical callback URL.
    path(
        'accounts/google/login/',
        OAuth2LoginView.adapter_view(BudgetGoogleOAuth2Adapter),
        name='google_login',
    ),
    path(
        'accounts/google/login/callback/',
        OAuth2CallbackView.adapter_view(BudgetGoogleOAuth2Adapter),
        name='google_callback',
    ),
    path('accounts/', include('allauth.urls')),
    path('', include('budgetbuddy.urls')),
]
