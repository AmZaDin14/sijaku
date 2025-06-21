from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("data.urls")),
    path("accounts/", include("accounts.urls")),
    path("admin/", admin.site.urls),
    path("__reload__/", include("django_browser_reload.urls")),
    path("penjadwalan/", include("penjadwalan.urls")),
]
