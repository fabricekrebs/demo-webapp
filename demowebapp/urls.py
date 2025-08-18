from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('django.contrib.auth.urls')),  # Built-in auth views
    path('api/', include('api.urls')),
    path('', include('tasks.urls')),
]