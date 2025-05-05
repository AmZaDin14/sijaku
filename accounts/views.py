# accounts/views.py
from django.contrib import auth
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from .forms import UserRegistrationForm

def register_user(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('login')  # atau ke halaman sukses lain
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')  # Redirect ke dashboard jika sudah login
        return super().get(request, *args, **kwargs)

def logout(request):
    auth.logout(request)
    return redirect('login')