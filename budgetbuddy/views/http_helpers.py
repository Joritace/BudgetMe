"""Helpers for in-page form submissions (no full reload)."""

from django.http import JsonResponse


def is_bb_ajax(request):
    return request.headers.get('X-BB-Ajax') == '1'


def ajax_success(message=''):
    return JsonResponse({'ok': True, 'message': message})


def ajax_form_errors(form, status=400):
    return JsonResponse(
        {
            'ok': False,
            'message': ' '.join(form.non_field_errors()) or 'Please fix the errors below.',
            'errors': form.errors,
        },
        status=status,
    )
