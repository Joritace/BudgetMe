from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_GET


def _redirect_static(request, path):
    return redirect(staticfiles_storage.url(path), permanent=False)


@require_GET
def apple_touch_icon(request):
    return _redirect_static(request, 'budgetbuddy/icons/apple-touch-icon.png')


@require_GET
def icon_192(request):
    return _redirect_static(request, 'budgetbuddy/icons/icon-192.png')


@require_GET
def icon_512(request):
    return _redirect_static(request, 'budgetbuddy/icons/icon-512.png')


@require_GET
def web_manifest(request):
    """Serve the PWA manifest with absolute icon URLs for Add to Home Screen."""
    icon_192 = request.build_absolute_uri(
        staticfiles_storage.url('budgetbuddy/icons/icon-192.png')
    )
    icon_512 = request.build_absolute_uri(
        staticfiles_storage.url('budgetbuddy/icons/icon-512.png')
    )
    return JsonResponse(
        {
            'name': 'BudgetMe',
            'short_name': 'BudgetMe',
            'description': 'Personal budget tracking for Uganda',
            'start_url': '/',
            'scope': '/',
            'display': 'standalone',
            'orientation': 'portrait',
            'background_color': '#e8faf2',
            'theme_color': '#3ecf8e',
            'icons': [
                {
                    'src': icon_192,
                    'sizes': '192x192',
                    'type': 'image/png',
                    'purpose': 'any',
                },
                {
                    'src': icon_512,
                    'sizes': '512x512',
                    'type': 'image/png',
                    'purpose': 'any maskable',
                },
            ],
        },
        content_type='application/manifest+json',
        headers={'Cache-Control': 'public, max-age=86400'},
    )


@require_GET
def service_worker(request):
    """Serve SW at site root so scope covers the whole app."""
    sw_path = finders.find('budgetbuddy/js/sw.js')
    if not sw_path:
        return HttpResponse('// Service worker not found', status=404, content_type='application/javascript')

    response = FileResponse(open(sw_path, 'rb'), content_type='application/javascript; charset=utf-8')
    response['Cache-Control'] = 'no-cache, max-age=0'
    response['Service-Worker-Allowed'] = '/'
    return response
