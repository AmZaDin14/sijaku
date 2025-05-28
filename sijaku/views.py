from django.shortcuts import render


def index(request):
    return render(request, 'sijaku/index.html')

def dashboard(request):
    return render(request, 'sijaku/dashboard/index.html')