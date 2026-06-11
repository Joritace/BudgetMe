from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from datetime import datetime, date


def _mock_user_data(user_id=None):
    """Replace with real DB lookups in integration"""
    return {
        'id': user_id or 1,
        'name': 'Test User',
        'monthly_income': 5000.0,
        'budget_categories': {
            'Housing': 1500.0,
            'Food': 600.0,
            'Transportation': 300.0,
            'Entertainment': 200.0,
            'Savings': 1000.0,
        }
    }


def _mock_expenses(user_id=None, year=None, month=None):
    """Replace with real DB lookups in integration"""
    sample = [
        {'date': date.today().replace(day=1), 'category': 'Housing', 'amount': 1400.0},
        {'date': date.today().replace(day=2), 'category': 'Food', 'amount': 250.0},
        {'date': date.today().replace(day=3), 'category': 'Transportation', 'amount': 120.0},
        {'date': date.today().replace(day=4), 'category': 'Entertainment', 'amount': 80.0},
        {'date': date.today().replace(day=5), 'category': 'Savings', 'amount': 900.0},
    ]
    return sample


def summarize_budget(user, expenses):
    """Calculate budget summary with spending analysis"""
    totals = {cat: 0.0 for cat in user['budget_categories'].keys()}
    for e in expenses:
        cat = e.get('category')
        amt = float(e.get('amount', 0.0))
        if cat in totals:
            totals[cat] += amt
        else:
            totals.setdefault(cat, 0.0)
            totals[cat] += amt

    overview = []
    for cat, allocated in user['budget_categories'].items():
        spent = totals.get(cat, 0.0)
        overview.append({
            'category': cat,
            'allocated': allocated,
            'spent': round(spent, 2),
            'remaining': round(allocated - spent, 2),
            'usage_percent': round((spent / allocated * 100) if allocated else 0, 1)
        })

    total_allocated = sum(user['budget_categories'].values())
    total_spent = sum(totals.values())

    return {
        'overview': overview,
        'total_allocated': round(total_allocated, 2),
        'total_spent': round(total_spent, 2),
        'month': date.today().strftime('%Y-%m')
    }


@require_http_methods(["GET"])
def dashboard_home(request):
    """Dashboard homepage view - displays budget summary and spending overview"""
    # Get optional query parameters
    user_id = request.GET.get('user_id', 1)
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        user_id = 1
    
    year = request.GET.get('year', None)
    month = request.GET.get('month', None)

    user = _mock_user_data(user_id)
    expenses = _mock_expenses(user_id, year, month)
    data = summarize_budget(user, expenses)

    context = {
        'user': user,
        'data': data,
    }

    # Try to render template, fallback to JSON
    if request.GET.get('json'):
        return JsonResponse({'user': user, 'data': data})
    
    return render(request, 'budgetbuddy/dashboard.html', context)
