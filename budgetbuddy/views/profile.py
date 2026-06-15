"""User profile view."""

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from budgetbuddy.constants import nav_items_for
from budgetbuddy.forms import ProfileForm
from budgetbuddy.services.profile import get_active_profile
from budgetbuddy.services.profile_page import build_profile_context


def _empty_profile_context():
    return {
        'has_budget': False,
        'first_name': 'Friend',
        'user': {'name': 'Guest'},
        'data': {'currency': 'UGX'},
        'nav_items': nav_items_for('profile'),
    }


@require_http_methods(['GET', 'POST'])
def profile_home(request):
    profile = get_active_profile(request)

    if not profile:
        return render(request, 'budgetbuddy/profile.html', _empty_profile_context())

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)

    context = build_profile_context(profile)
    context.update({
        'has_budget': True,
        'form': form,
        'nav_items': nav_items_for('profile'),
    })
    return render(request, 'budgetbuddy/profile.html', context)
