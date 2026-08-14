from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/accounts/", include("accounts.urls")),
    path("api/institutions/", include("institutions.urls")),
    path("api/companies/", include("companies.urls")),
    path("api/internships/", include("internships.urls")),
    path("api/notifications/", include("notifications.urls")),
    # FRONTEND ROUTES
    path("", include("core.frontend_urls")),
]

# Servir archivos estáticos y media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

