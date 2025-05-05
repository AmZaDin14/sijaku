from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect


# Create your views here.
def index(request):
    return render(request, "sijaku/index.html")

@login_required
def dashboard(request):
    if request.user.is_authenticated and request.user.role == 'admin': return redirect('/admin/')
    return render(request, "sijaku/dashboard/index.html")
