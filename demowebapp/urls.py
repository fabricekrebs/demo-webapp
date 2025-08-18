from django.contrib import admin
from django.urls import path, include
from .health import health_check, database_health

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('django.contrib.auth.urls')),  # Built-in auth views
    path('api/', include('api.urls')),
    path('health/', health_check, name='health_check'),  # Application health check
    path('health/database/', database_health, name='database_health'),  # Database-specific health check
    path('', include('tasks.urls')),
]