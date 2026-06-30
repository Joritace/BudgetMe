"""User profile view."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from budgetbuddy.constants import nav_items_for
from budgetbuddy.forms import ProfileForm
from budgetbuddy.services.page_context import build_guest_context
from budgetbuddy.services.profile import get_active_profile
from budgetbuddy.services.profile_page import build_profile_context


@login_required
@require_http_methods(['GET', 'POST'])
def profile_home(request):
    profile = get_active_profile(request)

    if not profile:
        return render(
            request,
            'budgetbuddy/profile.html',
            build_guest_context('profile', user=request.user),
        )

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
        'is_authenticated': True,
        'form': form,
        'nav_items': nav_items_for('profile'),
    })
    return render(request, 'budgetbuddy/profile.html', context)
