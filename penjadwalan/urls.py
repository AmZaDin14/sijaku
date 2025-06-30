from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/wd1/genetika/", views.genetika_wd1_view, name="genetika_wd1"),
    # path(
    #     "dashboard/wd1/genetika/progress/",
    #     views.genetika_progress,
    #     name="genetika_progress",
    # ),
    path("genetika/cancel/", views.genetika_cancel, name="genetika_cancel"),
    path("dashboard/wd1/genetika/start/", views.genetika_start, name="genetika_start"),
    path(
        "print-jadwal/",
        views.print_jadwal_per_semester,
        name="print_jadwal_per_semester",
    ),
    path("jadwal-genetika/", views.jadwal_genetika_list, name="jadwal_genetika_list"),
    path(
        "jadwal-genetika/<int:pk>/",
        views.jadwal_genetika_detail,
        name="jadwal_genetika_detail",
    ),
    path(
        "jadwal-genetika/<int:pk>/publish/",
        views.jadwal_genetika_publish,
        name="jadwal_genetika_publish",
    ),
]
