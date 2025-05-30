from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/dosen/', views.dosen_list, name='dosen_list'),
    path('dashboard/dosen/delete/<int:pk>/', views.dosen_delete, name='dosen_delete'),
    path('dashboard/dosen/tambah/', views.dosen_create, name='dosen_create'),
    path('dashboard/dosen/edit/<int:pk>/', views.dosen_update, name='dosen_update'),
    # CRUD MataKuliah
    path('dashboard/matakuliah/', views.matakuliah_list, name='matakuliah_list'),
    path('dashboard/matakuliah/tambah/', views.matakuliah_create, name='matakuliah_create'),
    path('dashboard/matakuliah/edit/<int:pk>/', views.matakuliah_update, name='matakuliah_update'),
    path('dashboard/matakuliah/delete/<int:pk>/', views.matakuliah_delete, name='matakuliah_delete'),
    # CRUD Tahun Akademik
    path('dashboard/tahunakademik/', views.tahunakademik_list, name='tahunakademik_list'),
    path('dashboard/tahunakademik/tambah/', views.tahunakademik_create, name='tahunakademik_create'),
    path('dashboard/tahunakademik/edit/<int:pk>/', views.tahunakademik_update, name='tahunakademik_update'),
    path('dashboard/tahunakademik/delete/<int:pk>/', views.tahunakademik_delete, name='tahunakademik_delete'),
    # CRUD Ruangan
    path('dashboard/ruangan/', views.ruangan_list, name='ruangan_list'),
    path('dashboard/ruangan/tambah/', views.ruangan_create, name='ruangan_create'),
    path('dashboard/ruangan/edit/<int:pk>/', views.ruangan_update, name='ruangan_update'),
    path('dashboard/ruangan/delete/<int:pk>/', views.ruangan_delete, name='ruangan_delete'),
]
