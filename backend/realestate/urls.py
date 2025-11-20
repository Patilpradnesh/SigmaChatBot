from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # This includes all routes from backend/api/urls.py
    path('api/', include('api.urls')),
]
