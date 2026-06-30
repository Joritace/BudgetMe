"""Shared test helpers."""

from django.contrib.auth import get_user_model
from django.urls import reverse


def login_test_user(client, *, email='jane@example.com', password='testpass123', first_name='Jane', last_name='Doe'):
    User = get_user_model()
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'username': email.split('@')[0],
            'first_name': first_name,
            'last_name': last_name,
        },
    )
    if not created:
        user.first_name = first_name
        user.last_name = last_name
        user.save(update_fields=['first_name', 'last_name'])
    user.set_password(password)
    user.save(update_fields=['password'])
    client.force_login(user)
    return user


def budget_setup_post_data(
    *,
    name='Jane Doe',
    income=2_500_000,
    frequency='monthly',
    goal=400_000,
    categories=None,
):
    categories = categories or [
        ('Rent', 800_000),
        ('Food & Market', 450_000),
    ]
    data = {
        'name': name,
        'income_amount': income,
        'income_frequency': frequency,
        'saving_goal_amount': goal,
        'form-TOTAL_FORMS': len(categories),
        'form-INITIAL_FORMS': 0,
        'form-MIN_NUM_FORMS': 0,
        'form-MAX_NUM_FORMS': 1000,
    }
    for i, (cat_name, amount) in enumerate(categories):
        data[f'form-{i}-name'] = cat_name
        data[f'form-{i}-allocated_amount'] = amount
    return data


def create_budget_via_form(client, **kwargs):
    login_test_user(client)
    return client.post(reverse('budget_setup'), budget_setup_post_data(**kwargs))


def set_profile_phones(client, mtn_phone='0770123456', airtel_phone='0750123456', name='Jane Doe'):
    return client.post(reverse('profile'), {
        'name': name,
        'mtn_phone': mtn_phone,
        'airtel_phone': airtel_phone,
    })
