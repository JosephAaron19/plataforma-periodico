from django.contrib import admin
from django.urls import path, include
from config.views import HealthCheckView, DatabaseHealthCheckView, RedisHealthCheckView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Authentication endpoints
    path('api/v1/auth/', include('apps.accounts.urls')),
    # Companies endpoints
    path('api/v1/companies/', include('apps.companies.urls')),
    # Plans endpoints
    path('api/v1/plans/', include('apps.plans.urls')),
    # Editions endpoints
    path('api/v1/', include('apps.editions.urls')),
    # Access endpoints
    path('api/v1/', include('apps.access.urls')),
    # Reading endpoints
    path('api/v1/', include('apps.reading.urls')),
    # Purchases endpoints (purchase, mock-confirm, my-purchases)
    path('api/v1/', include('apps.purchases.urls')),
    # Payments endpoints (webhooks)
    path('api/v1/payments/', include('apps.payments.urls')),
    # Versioned API Health Check endpoints

    path('api/v1/health/', HealthCheckView.as_view(), name='health_general'),
    path('api/v1/health/database/', DatabaseHealthCheckView.as_view(), name='health_database'),
    path('api/v1/health/redis/', RedisHealthCheckView.as_view(), name='health_redis'),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    # Ensure MEDIA_URL has correct slash prefix for static helper
    media_url = settings.MEDIA_URL
    if not media_url.startswith('/'):
        media_url = '/' + media_url
    urlpatterns += static(media_url, document_root=settings.MEDIA_ROOT)
