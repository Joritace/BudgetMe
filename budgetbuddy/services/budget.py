from datetime import date


def summarize_budget(user, expenses):
    totals = {cat: 0.0 for cat in user['budget_categories']}
    for expense in expenses:
        category = expense.get('category')
        amount = float(expense.get('amount', 0.0))
        if category in totals:
            totals[category] += amount
        else:
            totals.setdefault(category, 0.0)
            totals[category] += amount

    overview = []
    for category, allocated in user['budget_categories'].items():
        spent = totals.get(category, 0.0)
        overview.append({
            'category': category,
            'allocated': allocated,
            'spent': round(spent, 2),
            'remaining': round(allocated - spent, 2),
            'usage_percent': round((spent / allocated * 100) if allocated else 0, 1),
            'bar_percent': min(round((spent / allocated * 100) if allocated else 0), 100),
        })

    total_allocated = sum(user['budget_categories'].values())
    total_spent = sum(totals.values())

    return {
        'overview': overview,
        'total_allocated': round(total_allocated, 2),
        'total_spent': round(total_spent, 2),
        'total_remaining': round(total_allocated - total_spent, 2),
        'month': date.today().strftime('%B %Y'),
        'currency': user.get('currency', 'UGX'),
    }
