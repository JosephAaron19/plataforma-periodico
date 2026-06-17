from django.contrib import admin
from django.urls import path
from config.views import HealthCheckView, DatabaseHealthCheckView, RedisHealthCheckView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Versioned API Health Check endpoints
    path('api/v1/health/', HealthCheckView.as_view(), name='health_general'),
    path('api/v1/health/database/', DatabaseHealthCheckView.as_view(), name='health_database'),
    path('api/v1/health/redis/', RedisHealthCheckView.as_view(), name='health_redis'),
]
