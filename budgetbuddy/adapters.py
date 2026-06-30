"""django-allauth adapters for BudgetMe."""

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class BudgetAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        return '/'


class BudgetSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        email = data.get('email') or user.email
        if email and not user.username:
            user.username = email.split('@')[0][:150]
        first_name = data.get('first_name') or data.get('given_name', '')
        last_name = data.get('last_name') or data.get('family_name', '')
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        return user
