from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/admin/dosen/', views.dosen_list, name='dosen_list'),
    path('dashboard/admin/dosen/delete/<int:pk>/', views.dosen_delete, name='dosen_delete'),
    path('dashboard/admin/dosen/tambah/', views.dosen_create, name='dosen_create'),
    path('dashboard/admin/dosen/edit/<int:pk>/', views.dosen_update, name='dosen_update'),
]
