from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/dosen/", views.dosen_list, name="dosen_list"),
    path("dashboard/dosen/delete/<int:pk>/", views.dosen_delete, name="dosen_delete"),
    path("dashboard/dosen/tambah/", views.dosen_create, name="dosen_create"),
    path("dashboard/dosen/edit/<int:pk>/", views.dosen_update, name="dosen_update"),
    path(
        "dashboard/dosen/upload-csv/",
        views.dosen_upload_csv,
        name="dosen_upload_csv",
    ),
    # CRUD MataKuliah
    path("dashboard/matakuliah/", views.matakuliah_list, name="matakuliah_list"),
    path(
        "dashboard/matakuliah/tambah/",
        views.matakuliah_create,
        name="matakuliah_create",
    ),
    path(
        "dashboard/matakuliah/edit/<int:pk>/",
        views.matakuliah_update,
        name="matakuliah_update",
    ),
    path(
        "dashboard/matakuliah/delete/<int:pk>/",
        views.matakuliah_delete,
        name="matakuliah_delete",
    ),
    path(
        "dashboard/matakuliah/upload-excel/",
        views.matakuliah_upload_excel,
        name="matakuliah_upload_excel",
    ),
    # CRUD Tahun Akademik
    path(
        "dashboard/tahunakademik/", views.tahunakademik_list, name="tahunakademik_list"
    ),
    path(
        "dashboard/tahunakademik/tambah/",
        views.tahunakademik_create,
        name="tahunakademik_create",
    ),
    path(
        "dashboard/tahunakademik/edit/<int:pk>/",
        views.tahunakademik_update,
        name="tahunakademik_update",
    ),
    path(
        "dashboard/tahunakademik/delete/<int:pk>/",
        views.tahunakademik_delete,
        name="tahunakademik_delete",
    ),
    # CRUD Ruangan
    path("dashboard/ruangan/", views.ruangan_list, name="ruangan_list"),
    path("dashboard/ruangan/tambah/", views.ruangan_create, name="ruangan_create"),
    path(
        "dashboard/ruangan/edit/<int:pk>/", views.ruangan_update, name="ruangan_update"
    ),
    path(
        "dashboard/ruangan/delete/<int:pk>/",
        views.ruangan_delete,
        name="ruangan_delete",
    ),
    # Pemetaan Dosen-MK
    path("dashboard/pemetaan/", views.pemetaan_list, name="pemetaan_list"),
    path(
        "dashboard/pemetaan/tambah-mk/",
        views.pemetaan_edit_mk,
        name="pemetaan_tambah_mk",
    ),
    path(
        "dashboard/pemetaan/edit-dosen/<int:pk>/",
        views.pemetaan_edit_dosen,
        name="pemetaan_edit_dosen",
    ),
    # CRUD Peminatan
    path("dashboard/peminatan/", views.peminatan_list, name="peminatan_list"),
    path(
        "dashboard/peminatan/tambah/", views.peminatan_create, name="peminatan_create"
    ),
    path(
        "dashboard/peminatan/edit/<int:pk>/",
        views.peminatan_update,
        name="peminatan_update",
    ),
    path(
        "dashboard/peminatan/delete/<int:pk>/",
        views.peminatan_delete,
        name="peminatan_delete",
    ),
]
