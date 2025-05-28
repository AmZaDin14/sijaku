from django.shortcuts import render, redirect, get_object_or_404
from .models import Dosen, Jabatan, MataKuliah
from .forms import DosenForm
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.http import require_http_methods


def index(request):
    return render(request, 'sijaku/index.html')

def dashboard(request):
    return render(request, 'sijaku/dashboard/index.html')

def dosen_list(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    dosen = Dosen.objects.all()
    return render(request, 'sijaku/dashboard/admin/dosen.html', {'dosen_list': dosen})

@require_http_methods(["POST"])
def dosen_delete(request, pk):
    if not request.user.is_superuser:
        return redirect('dashboard')
    dosen = get_object_or_404(Dosen, pk=pk)
    dosen.delete()
    messages.success(request, "Dosen berhasil dihapus.")
    return redirect(reverse('dosen_list'))

def dosen_create(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
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
    if not request.user.is_superuser:
        return redirect('dashboard')
    dosen = get_object_or_404(Dosen, pk=pk)
    password_message = None
    password_error = None
    # Proses ubah password user jika ada query param ubah_password=1
    if request.method == 'POST' and request.GET.get('ubah_password') == '1' and dosen.user:
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if not new_password or not confirm_password:
            password_error = 'Password tidak boleh kosong.'
        elif new_password != confirm_password:
            password_error = 'Password dan konfirmasi tidak sama.'
        else:
            dosen.user.set_password(new_password)
            dosen.user.save()
            password_message = 'Password berhasil diubah.'
            return redirect('dosen_list')
    # Proses update data dosen
    elif request.method == 'POST':
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
        'selected_jabatans': selected_jabatans,
        'password_message': password_message,
        'password_error': password_error,
    })

def matakuliah_list(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    matakuliah = MataKuliah.objects.all()
    return render(request, 'sijaku/dashboard/admin/matakuliah.html', {'matakuliah_list': matakuliah})

def matakuliah_create(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    if request.method == 'POST':
        from .forms import MataKuliahForm
        form = MataKuliahForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('matakuliah_list')
    else:
        from .forms import MataKuliahForm
        form = MataKuliahForm()
    return render(request, 'sijaku/dashboard/admin/matakuliah_form.html', {'form': form})

def matakuliah_update(request, pk):
    if not request.user.is_superuser:
        return redirect('dashboard')
    matakuliah = get_object_or_404(MataKuliah, pk=pk)
    from .forms import MataKuliahForm
    if request.method == 'POST':
        form = MataKuliahForm(request.POST, instance=matakuliah)
        if form.is_valid():
            form.save()
            return redirect('matakuliah_list')
    else:
        form = MataKuliahForm(instance=matakuliah)
    return render(request, 'sijaku/dashboard/admin/matakuliah_form.html', {'form': form, 'edit': True, 'matakuliah': matakuliah})

@require_http_methods(["POST"])
def matakuliah_delete(request, pk):
    if not request.user.is_superuser:
        return redirect('dashboard')
    matakuliah = get_object_or_404(MataKuliah, pk=pk)
    matakuliah.delete()
    messages.success(request, "Mata Kuliah berhasil dihapus.")
    return redirect('matakuliah_list')