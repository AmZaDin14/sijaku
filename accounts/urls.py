# accounts/urls.py
from django.urls import path

from .views import register_user, CustomLoginView, logout

urlpatterns = [
    path('register/', register_user, name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', logout, name='logout'),
]
