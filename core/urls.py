from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def api_root(request):
    return JsonResponse({
        'name': 'Logistics Management API',
        'status': 'healthy',
        'version': 'v1',
        'endpoints': {
            'admin': '/admin/',
            'auth_login': '/api/v1/auth/login/',
            'auth_refresh': '/api/v1/auth/token/refresh/',
            'users': '/api/v1/users/',
            'user_me': '/api/v1/users/me/',
            'shipments': '/api/v1/shipments/',
            'public_tracking': '/api/v1/track/{tracking_number}/',
            'health_check': '/health/',
        }
    })


def health_check(request):
    return JsonResponse({'status': 'ok', 'service': 'logistics-backend'})


urlpatterns = [
    path('', api_root, name='api_root'),
    path('health/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('api/v1/', include('logistics.urls')),
]

