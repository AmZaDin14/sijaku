from django.shortcuts import render, redirect, get_object_or_404
from .models import Dosen, Jabatan
from .forms import DosenForm
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.http import require_http_methods


def index(request):
    return render(request, 'sijaku/index.html')

def dashboard(request):
    return render(request, 'sijaku/dashboard/index.html')

def dosen_list(request):
    dosen = Dosen.objects.all()
    return render(request, 'sijaku/dashboard/admin/dosen.html', {'dosen_list': dosen})

@require_http_methods(["POST"])
def dosen_delete(request, pk):
    dosen = get_object_or_404(Dosen, pk=pk)
    dosen.delete()
    messages.success(request, "Dosen berhasil dihapus.")
    return redirect(reverse('dosen_list'))

def dosen_create(request):
    if request.method == 'POST':
        form = DosenForm(request.POST)
        if form.is_valid():
            dosen = form.save()
            # Update jabatan assignment
            selected_jabatans = request.POST.getlist('jabatans')
            Jabatan.objects.filter(id__in=selected_jabatans).update(dosen=dosen)
            Jabatan.objects.exclude(id__in=selected_jabatans).filter(dosen=dosen).update(dosen=None)
            return redirect('dosen_list')
    else:
        form = DosenForm()
    jabatans = Jabatan.objects.all()
    selected_jabatans = []
    return render(request, 'sijaku/dashboard/admin/dosen_form.html', {
        'form': form,
        'jabatans': jabatans,
        'selected_jabatans': selected_jabatans
    })

def dosen_update(request, pk):
    dosen = get_object_or_404(Dosen, pk=pk)
    if request.method == 'POST':
        form = DosenForm(request.POST, instance=dosen)
        if form.is_valid():
            dosen = form.save()
            selected_jabatans = request.POST.getlist('jabatans')
            # Set jabatan ke dosen ini
            Jabatan.objects.filter(id__in=selected_jabatans).update(dosen=dosen)
            # Hapus jabatan yang tidak dipilih dari dosen ini
            Jabatan.objects.exclude(id__in=selected_jabatans).filter(dosen=dosen).update(dosen=None)
            return redirect('dosen_list')
    else:
        form = DosenForm(instance=dosen)
    jabatans = Jabatan.objects.all()
    selected_jabatans = list(Jabatan.objects.filter(dosen=dosen).values_list('id', flat=True))
    return render(request, 'sijaku/dashboard/admin/dosen_form.html', {
        'form': form,
        'edit': True,
        'dosen': dosen,
        'jabatans': jabatans,
        'selected_jabatans': selected_jabatans
    })