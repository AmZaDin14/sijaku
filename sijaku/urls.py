from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/admin/dosen/', views.dosen_list, name='dosen_list'),
    path('dashboard/admin/dosen/delete/<int:pk>/', views.dosen_delete, name='dosen_delete'),
    path('dashboard/admin/dosen/tambah/', views.dosen_create, name='dosen_create'),
    path('dashboard/admin/dosen/edit/<int:pk>/', views.dosen_update, name='dosen_update'),
    # CRUD MataKuliah
    path('dashboard/admin/matakuliah/', views.matakuliah_list, name='matakuliah_list'),
    path('dashboard/admin/matakuliah/tambah/', views.matakuliah_create, name='matakuliah_create'),
    path('dashboard/admin/matakuliah/edit/<int:pk>/', views.matakuliah_update, name='matakuliah_update'),
    path('dashboard/admin/matakuliah/delete/<int:pk>/', views.matakuliah_delete, name='matakuliah_delete'),
    # CRUD Tahun Akademik
    path('dashboard/admin/tahunakademik/', views.tahunakademik_list, name='tahunakademik_list'),
    path('dashboard/admin/tahunakademik/tambah/', views.tahunakademik_create, name='tahunakademik_create'),
    path('dashboard/admin/tahunakademik/edit/<int:pk>/', views.tahunakademik_update, name='tahunakademik_update'),
    path('dashboard/admin/tahunakademik/delete/<int:pk>/', views.tahunakademik_delete, name='tahunakademik_delete'),
]
