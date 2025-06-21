from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/wd1/genetika/", views.genetika_wd1_view, name="genetika_wd1"),
    path(
        "dashboard/wd1/genetika/progress/",
        views.genetika_progress,
        name="genetika_progress",
    ),
    path("genetika/cancel/", views.genetika_cancel, name="genetika_cancel"),
    path("dashboard/wd1/genetika/start/", views.genetika_start, name="genetika_start"),
]
