from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def auth_status(request):
    return JsonResponse({'authenticated': request.user.is_authenticated})
