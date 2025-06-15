import csv
import json
from collections import defaultdict
from datetime import datetime, time, timedelta

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.decorators.http import require_http_methods

from .forms import DosenForm, JadwalHarianForm
from .models import (
    Dosen,
    Jabatan,
    Jadwal,
    JadwalHarian,
    Kelas,
    MataKuliah,
    PemetaanDosenMK,
    Peminatan,  # pastikan sudah diimpor
    Ruangan,
    TahunAkademik,
)


def index(request):
    return render(request, "sijaku/index.html")


@login_required
def dashboard(request):
    return render(request, "sijaku/dashboard/index.html")


def dosen_list(request):
    if not request.user.is_superuser:
        return redirect("dashboard")
    dosen = Dosen.objects.all()
    return render(request, "sijaku/dashboard/admin/dosen.html", {"dosen_list": dosen})


@require_http_methods(["POST"])
def dosen_delete(request, pk):
    if not request.user.is_superuser:
        return redirect("dashboard")
    dosen = get_object_or_404(Dosen, pk=pk)
    dosen.delete()
    messages.success(request, "Dosen berhasil dihapus.")
    return redirect(reverse("dosen_list"))


def dosen_create(request):
    if not request.user.is_superuser:
        return redirect("dashboard")
    if request.method == "POST":
        form = DosenForm(request.POST)
        if form.is_valid():
            dosen = form.save()
            # Update jabatan assignment
            selected_jabatans = request.POST.getlist("jabatans")
            Jabatan.objects.filter(id__in=selected_jabatans).update(dosen=dosen)
            Jabatan.objects.exclude(id__in=selected_jabatans).filter(
                dosen=dosen
            ).update(dosen=None)
            return redirect("dosen_list")
    else:
        form = DosenForm()
    jabatans = Jabatan.objects.all()
    selected_jabatans = []
    return render(
        request,
        "sijaku/dashboard/admin/dosen_form.html",
        {"form": form, "jabatans": jabatans, "selected_jabatans": selected_jabatans},
    )


def dosen_update(request, pk):
    if not request.user.is_superuser:
        return redirect("dashboard")
    dosen = get_object_or_404(Dosen, pk=pk)
    password_message = None
    password_error = None
    # Proses ubah password user jika ada query param ubah_password=1
    if (
        request.method == "POST"
        and request.GET.get("ubah_password") == "1"
        and dosen.user
    ):
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")
        if not new_password or not confirm_password:
            password_error = "Password tidak boleh kosong."
        elif new_password != confirm_password:
            password_error = "Password dan konfirmasi tidak sama."
        else:
            dosen.user.set_password(new_password)
            dosen.user.save()
            password_message = "Password berhasil diubah."
            return redirect("dosen_list")
    # Proses update data dosen
    elif request.method == "POST":
        form = DosenForm(request.POST, instance=dosen)
        if form.is_valid():
            dosen = form.save()
            selected_jabatans = request.POST.getlist("jabatans")
            # Set jabatan ke dosen ini
            Jabatan.objects.filter(id__in=selected_jabatans).update(dosen=dosen)
            # Hapus jabatan yang tidak dipilih dari dosen ini
            Jabatan.objects.exclude(id__in=selected_jabatans).filter(
                dosen=dosen
            ).update(dosen=None)
            return redirect("dosen_list")
    else:
        form = DosenForm(instance=dosen)
    jabatans = Jabatan.objects.all()
    selected_jabatans = list(
        Jabatan.objects.filter(dosen=dosen).values_list("id", flat=True)
    )
    return render(
        request,
        "sijaku/dashboard/admin/dosen_form.html",
        {
            "form": form,
            "edit": True,
            "dosen": dosen,
            "jabatans": jabatans,
            "selected_jabatans": selected_jabatans,
            "password_message": password_message,
            "password_error": password_error,
        },
    )


def matakuliah_list(request):
    if not request.user.is_superuser:
        return redirect("dashboard")
    matakuliah = MataKuliah.objects.all()
    return render(
        request,
        "sijaku/dashboard/admin/matakuliah.html",
        {"matakuliah_list": matakuliah},
    )


def matakuliah_create(request):
    if not request.user.is_superuser:
        return redirect("dashboard")
    if request.method == "POST":
        from .forms import MataKuliahForm

        form = MataKuliahForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("matakuliah_list")
    else:
        from .forms import MataKuliahForm

        form = MataKuliahForm()
    return render(
        request, "sijaku/dashboard/admin/matakuliah_form.html", {"form": form}
    )


def matakuliah_update(request, pk):
    if not request.user.is_superuser:
        return redirect("dashboard")
    matakuliah = get_object_or_404(MataKuliah, pk=pk)
    from .forms import MataKuliahForm

    if request.method == "POST":
        form = MataKuliahForm(request.POST, instance=matakuliah)
        if form.is_valid():
            form.save()
            return redirect("matakuliah_list")
    else:
        form = MataKuliahForm(instance=matakuliah)
    return render(
        request,
        "sijaku/dashboard/admin/matakuliah_form.html",
        {"form": form, "edit": True, "matakuliah": matakuliah},
    )


@require_http_methods(["POST"])
def matakuliah_delete(request, pk):
    if not request.user.is_superuser:
        return redirect("dashboard")
    matakuliah = get_object_or_404(MataKuliah, pk=pk)
    matakuliah.delete()
    messages.success(request, "Mata Kuliah berhasil dihapus.")
    return redirect("matakuliah_list")


def is_kaprodi(user):
    return hasattr(user, "dosen") and user.dosen.jabatan.filter(nama="kaprodi").exists()


def tahunakademik_list(request):
    if not request.user.is_authenticated or not is_kaprodi(request.user):
        return redirect("dashboard")
    tahunakademik = TahunAkademik.objects.all()
    return render(
        request,
        "sijaku/dashboard/admin/tahunakademik.html",
        {"tahunakademik_list": tahunakademik},
    )


def tahunakademik_create(request):
    if not request.user.is_authenticated or not is_kaprodi(request.user):
        return redirect("dashboard")
    from .forms import TahunAkademikForm

    if request.method == "POST":
        form = TahunAkademikForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("tahunakademik_list")
    else:
        form = TahunAkademikForm()
    return render(
        request, "sijaku/dashboard/admin/tahunakademik_form.html", {"form": form}
    )


def tahunakademik_update(request, pk):
    if not request.user.is_authenticated or not is_kaprodi(request.user):
        return redirect("dashboard")
    tahunakademik = get_object_or_404(TahunAkademik, pk=pk)
    from .forms import TahunAkademikForm

    if request.method == "POST":
        form = TahunAkademikForm(request.POST, instance=tahunakademik)
        if form.is_valid():
            form.save()
            return redirect("tahunakademik_list")
    else:
        form = TahunAkademikForm(instance=tahunakademik)
    return render(
        request,
        "sijaku/dashboard/admin/tahunakademik_form.html",
        {"form": form, "edit": True, "tahunakademik": tahunakademik},
    )


@require_http_methods(["POST"])
def tahunakademik_delete(request, pk):
    if not request.user.is_authenticated or not is_kaprodi(request.user):
        return redirect("dashboard")
    tahunakademik = get_object_or_404(TahunAkademik, pk=pk)
    tahunakademik.delete()
    messages.success(request, "Tahun Akademik berhasil dihapus.")
    return redirect("tahunakademik_list")


def ruangan_list(request):
    if not request.user.is_superuser:
        return redirect("dashboard")
    ruangan = Ruangan.objects.all()
    return render(
        request, "sijaku/dashboard/admin/ruangan.html", {"ruangan_list": ruangan}
    )


def ruangan_create(request):
    if not request.user.is_superuser:
        return redirect("dashboard")
    from .forms import RuanganForm

    if request.method == "POST":
        form = RuanganForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("ruangan_list")
    else:
        form = RuanganForm()
    return render(request, "sijaku/dashboard/admin/ruangan_form.html", {"form": form})


def ruangan_update(request, pk):
    if not request.user.is_superuser:
        return redirect("dashboard")
    ruangan = get_object_or_404(Ruangan, pk=pk)
    from .forms import RuanganForm

    if request.method == "POST":
        form = RuanganForm(request.POST, instance=ruangan)
        if form.is_valid():
            form.save()
            return redirect("ruangan_list")
    else:
        form = RuanganForm(instance=ruangan)
    return render(
        request,
        "sijaku/dashboard/admin/ruangan_form.html",
        {"form": form, "edit": True, "ruangan": ruangan},
    )


@require_http_methods(["POST"])
def ruangan_delete(request, pk):
    if not request.user.is_superuser:
        return redirect("dashboard")
    ruangan = get_object_or_404(Ruangan, pk=pk)
    ruangan.delete()
    messages.success(request, "Ruangan berhasil dihapus.")
    return redirect("ruangan_list")


def pemetaan_list(request):
    if not is_kaprodi(request.user):
        return redirect("dashboard")
    tahun_aktif = TahunAkademik.objects.filter(aktif=True).first()
    if not tahun_aktif:
        return render(
            request, "sijaku/dashboard/admin/pemetaan.html", {"tahun_aktif": None}
        )
    daftar = PemetaanDosenMK.objects.filter(tahun_akademik=tahun_aktif).select_related(
        "matakuliah", "dosen_pengampu"
    )
    return render(
        request,
        "sijaku/dashboard/admin/pemetaan.html",
        {"tahun_aktif": tahun_aktif, "pemetaan_list": daftar},
    )


def pemetaan_edit_mk(request):
    if not is_kaprodi(request.user):
        return redirect("dashboard")
    tahun_aktif = TahunAkademik.objects.filter(aktif=True).first()
    if not tahun_aktif:
        return redirect("pemetaan_list")
    if tahun_aktif.semester == "genap":
        matakuliah_qs = MataKuliah.objects.filter(semester__in=[2, 4, 6, 8, 10, 12, 14])
    else:
        matakuliah_qs = MataKuliah.objects.filter(semester__in=[1, 3, 5, 7, 9, 11, 13])
    # Exclude MK yang sudah ada di tahun aktif
    existing_ids = set(
        PemetaanDosenMK.objects.filter(tahun_akademik=tahun_aktif).values_list(
            "matakuliah_id", flat=True
        )
    )
    # Mata kuliah yang sudah dipetakan (selected)
    selected_mk = [
        {"id": mk.pk, "label": f"{mk.kode} - {mk.nama}", "_checked": False}
        for mk in matakuliah_qs
        if mk.pk in existing_ids
    ]
    # Mata kuliah yang belum dipetakan (available)
    available_mk = [
        {"id": mk.pk, "label": f"{mk.kode} - {mk.nama}", "_checked": False}
        for mk in matakuliah_qs
        if mk.pk not in existing_ids
    ]
    if request.method == "POST":
        mk_ids = set(map(int, request.POST.getlist("matakuliah_ids")))
        # Tambah yang baru dipilih
        for mk_id in mk_ids:
            if not PemetaanDosenMK.objects.filter(
                tahun_akademik=tahun_aktif, matakuliah_id=mk_id
            ).exists():
                PemetaanDosenMK.objects.create(
                    tahun_akademik=tahun_aktif, matakuliah_id=mk_id
                )
        # Hapus yang tidak dipilih lagi
        for mk_id in existing_ids:
            if mk_id not in mk_ids:
                PemetaanDosenMK.objects.filter(
                    tahun_akademik=tahun_aktif, matakuliah_id=mk_id
                ).delete()
        return redirect("pemetaan_list")
    return render(
        request,
        "sijaku/dashboard/admin/pemetaan_edit_mk.html",
        {
            "tahun_aktif": tahun_aktif,
            "available_mk": json.dumps(available_mk),
            "selected_mk": json.dumps(selected_mk),
        },
    )


def pemetaan_edit_dosen(request, pk):
    if not is_kaprodi(request.user):
        return redirect("dashboard")
    pemetaan = PemetaanDosenMK.objects.select_related(
        "matakuliah", "dosen_pengampu"
    ).get(pk=pk)

    class EditDosenForm(forms.ModelForm):
        class Meta:
            model = PemetaanDosenMK
            fields = ["dosen_pengampu"]
            widgets = {
                "dosen_pengampu": forms.Select(
                    attrs={"class": "select select-bordered w-full"}
                ),
            }

    if request.method == "POST":
        form = EditDosenForm(request.POST, instance=pemetaan)
        if form.is_valid():
            form.save()
            messages.success(request, "Dosen pengampu berhasil diubah.")
            return redirect("pemetaan_list")
    else:
        form = EditDosenForm(instance=pemetaan)
    return render(
        request,
        "sijaku/dashboard/admin/pemetaan_edit_dosen.html",
        {"form": form, "pemetaan": pemetaan},
    )


def matakuliah_upload_excel(request):
    if not request.user.is_superuser:
        return redirect("dashboard")
    if request.method == "POST" and request.FILES.get("excel_file"):
        file = request.FILES["excel_file"]
        # Support CSV only for simplicity
        if file.name.endswith(".csv"):
            decoded = file.read().decode("utf-8").splitlines()
            reader = csv.DictReader(decoded)
            count = 0
            for row in reader:
                kode = row.get("Kode")
                nama = row.get("Nama")
                sks = row.get("SKS")
                semester = row.get("Semester")
                tipe = row.get("Tipe")
                peminatan_kode = row.get("Peminatan")
                if kode and nama and sks and semester and tipe:
                    peminatan = None
                    if peminatan_kode and peminatan_kode != "-":
                        peminatan = Peminatan.objects.filter(
                            kode=peminatan_kode.strip()
                        ).first()
                    MataKuliah.objects.get_or_create(
                        kode=kode.strip(),
                        defaults={
                            "nama": nama.strip(),
                            "sks": int(sks),
                            "semester": int(semester),
                            "tipe": tipe.strip(),
                            "peminatan": peminatan,
                        },
                    )
                    count += 1
            messages.success(
                request, f"Berhasil menambahkan {count} mata kuliah dari file."
            )
        else:
            messages.error(request, "Format file tidak didukung. Upload file .csv.")
    return redirect("matakuliah_list")


def dosen_upload_csv(request):
    if not request.user.is_superuser:
        return redirect("dashboard")
    if request.method == "POST" and request.FILES.get("csv_file"):
        file = request.FILES["csv_file"]
        decoded = file.read().decode("utf-8").splitlines()
        reader = csv.DictReader(decoded)
        count = 0
        for row in reader:
            nidn = row.get("NIDN")
            nama = row.get("Nama")
            if nidn and nama:
                Dosen.objects.get_or_create(
                    nidn=nidn.strip(),
                    defaults={"nama": nama.strip()},
                )
                count += 1
        messages.success(request, f"Berhasil menambahkan {count} dosen dari file.")
    return redirect("dosen_list")


def peminatan_list(request):
    if not request.user.is_superuser:
        return redirect("dashboard")
    daftar = Peminatan.objects.all()
    return render(
        request, "sijaku/dashboard/admin/peminatan.html", {"peminatan_list": daftar}
    )


def peminatan_create(request):
    if not request.user.is_superuser:
        return redirect("dashboard")
    from .forms import PeminatanForm

    if request.method == "POST":
        form = PeminatanForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("peminatan_list")
    else:
        form = PeminatanForm()
    return render(request, "sijaku/dashboard/admin/peminatan_form.html", {"form": form})


def peminatan_update(request, pk):
    if not request.user.is_superuser:
        return redirect("dashboard")
    from .forms import PeminatanForm

    peminatan = get_object_or_404(Peminatan, pk=pk)
    if request.method == "POST":
        form = PeminatanForm(request.POST, instance=peminatan)
        if form.is_valid():
            form.save()
            return redirect("peminatan_list")
    else:
        form = PeminatanForm(instance=peminatan)
    return render(
        request,
        "sijaku/dashboard/admin/peminatan_form.html",
        {"form": form, "edit": True, "peminatan": peminatan},
    )


@require_http_methods(["POST"])
def peminatan_delete(request, pk):
    if not request.user.is_superuser:
        return redirect("dashboard")
    peminatan = get_object_or_404(Peminatan, pk=pk)
    peminatan.delete()
    return redirect("peminatan_list")


@require_http_methods(["POST"])
def ruangan_upload_csv(request):
    if not request.user.is_superuser:
        return redirect("dashboard")
    if request.method == "POST" and request.FILES.get("csv_file"):
        file = request.FILES["csv_file"]
        if file.name.endswith(".csv"):
            decoded = file.read().decode("utf-8").splitlines()
            reader = csv.DictReader(decoded)
            count = 0
            for row in reader:
                nama = row.get("Nama")
                jenis = row.get("Jenis")
                kapasitas = row.get("Kapasitas")
                if nama and jenis and kapasitas:
                    Ruangan.objects.get_or_create(
                        nama=nama.strip(),
                        defaults={
                            "jenis": jenis.strip(),
                            "kapasitas": int(kapasitas),
                        },
                    )
                    count += 1
            messages.success(
                request, f"Berhasil menambahkan {count} ruangan dari file."
            )
        else:
            messages.error(request, "Format file harus CSV.")
    return redirect("ruangan_list")


def kelas_list(request):
    if not request.user.is_superuser:
        return redirect("dashboard")
    daftar = Kelas.objects.select_related("peminatan").all()
    return render(request, "sijaku/dashboard/admin/kelas.html", {"kelas_list": daftar})


def kelas_create(request):
    if not request.user.is_superuser:
        return redirect("dashboard")
    from .forms import KelasForm

    if request.method == "POST":
        form = KelasForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("kelas_list")
    else:
        form = KelasForm()
    return render(request, "sijaku/dashboard/admin/kelas_form.html", {"form": form})


def kelas_update(request, pk):
    if not request.user.is_superuser:
        return redirect("dashboard")
    from .forms import KelasForm

    kelas = get_object_or_404(Kelas, pk=pk)
    if request.method == "POST":
        form = KelasForm(request.POST, instance=kelas)
        if form.is_valid():
            form.save()
            return redirect("kelas_list")
    else:
        form = KelasForm(instance=kelas)
    return render(
        request,
        "sijaku/dashboard/admin/kelas_form.html",
        {"form": form, "edit": True, "kelas": kelas},
    )


@require_http_methods(["POST"])
def kelas_delete(request, pk):
    if not request.user.is_superuser:
        return redirect("dashboard")
    kelas = get_object_or_404(Kelas, pk=pk)
    kelas.delete()
    return redirect("kelas_list")


@require_http_methods(["POST"])
def kelas_upload_csv(request):
    if not request.user.is_superuser:
        return redirect("dashboard")
    if request.method == "POST" and request.FILES.get("csv_file"):
        file = request.FILES["csv_file"]
        if file.name.endswith(".csv"):
            decoded = file.read().decode("utf-8").splitlines()
            reader = csv.DictReader(decoded)
            count = 0
            for row in reader:
                tahun_angkatan = row.get("Tahun Angkatan")
                nama = row.get("Nama")
                peminatan_kode = row.get("Peminatan")
                if tahun_angkatan and nama:
                    peminatan = None
                    if peminatan_kode and peminatan_kode != "-":
                        peminatan = Peminatan.objects.filter(
                            kode=peminatan_kode.strip()
                        ).first()
                    Kelas.objects.get_or_create(
                        tahun_angkatan=int(tahun_angkatan),
                        nama=nama.strip(),
                        defaults={"peminatan": peminatan},
                    )
                    count += 1
            messages.success(request, f"Berhasil menambahkan {count} kelas dari file.")
        else:
            messages.error(request, "Format file harus CSV.")
    return redirect("kelas_list")


def jadwalharian_list(request):
    if not request.user.is_superuser:
        return redirect("dashboard")
    jadwal = JadwalHarian.objects.all()
    return render(
        request,
        "sijaku/dashboard/admin/jadwalharian.html",
        {"jadwalharian_list": jadwal},
    )


def jadwalharian_create(request):
    if not request.user.is_superuser:
        return redirect("dashboard")
    if request.method == "POST":
        form = JadwalHarianForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("jadwalharian_list")
    else:
        form = JadwalHarianForm()
    return render(
        request, "sijaku/dashboard/admin/jadwalharian_form.html", {"form": form}
    )


def jadwalharian_update(request, pk):
    if not request.user.is_superuser:
        return redirect("dashboard")
    jadwal = get_object_or_404(JadwalHarian, pk=pk)
    if request.method == "POST":
        form = JadwalHarianForm(request.POST, instance=jadwal)
        if form.is_valid():
            form.save()
            return redirect("jadwalharian_list")
    else:
        form = JadwalHarianForm(instance=jadwal)
    return render(
        request,
        "sijaku/dashboard/admin/jadwalharian_form.html",
        {"form": form, "edit": True, "jadwalharian": jadwal},
    )


@require_http_methods(["POST"])
def jadwalharian_delete(request, pk):
    if not request.user.is_superuser:
        return redirect("dashboard")
    jadwal = get_object_or_404(JadwalHarian, pk=pk)
    jadwal.delete()
    messages.success(request, "Jadwal Harian berhasil dihapus.")
    return redirect("jadwalharian_list")


def jadwalharian_upload_csv(request):
    if not request.user.is_superuser:
        return redirect("dashboard")
    if request.method == "POST" and request.FILES.get("csv_file"):
        file = request.FILES["csv_file"]
        if file.name.endswith(".csv"):
            decoded = file.read().decode("utf-8").splitlines()
            reader = csv.DictReader(decoded)
            count = 0
            for row in reader:
                hari = row.get("Hari")
                jam_mulai = row.get("Jam Mulai")
                jam_selesai = row.get("Jam Selesai")
                istirahat_mulai = row.get("Istirahat Mulai")
                istirahat_selesai = row.get("Istirahat Selesai")
                if (
                    hari is not None
                    and jam_mulai
                    and jam_selesai
                    and istirahat_mulai
                    and istirahat_selesai
                ):
                    # Cari index hari dari pilihan HARI_CHOICES
                    hari_idx = None
                    for idx, label in JadwalHarian.HARI_CHOICES:
                        if label.lower() == hari.strip().lower():
                            hari_idx = idx
                            break
                    if hari_idx is not None:
                        obj, created = JadwalHarian.objects.update_or_create(
                            hari=hari_idx,
                            defaults={
                                "jam_mulai": jam_mulai,
                                "jam_selesai": jam_selesai,
                                "istirahat_mulai": istirahat_mulai,
                                "istirahat_selesai": istirahat_selesai,
                            },
                        )
                        count += 1
            messages.success(
                request,
                f"Berhasil menambahkan/memperbarui {count} jadwal harian dari file.",
            )
        else:
            messages.error(request, "Format file tidak didukung. Upload file .csv.")
    return redirect("jadwalharian_list")


class JadwalMasterView(View):
    template_name = "sijaku/dashboard/jadwal_master.html"

    def get(self, request, *args, **kwargs):
        context = {
            "jadwal_ditemukan": False,
            "tahun_akademik_aktif": None,
            "jadwal_per_hari": {},
            "time_slots": [],
        }

        try:
            tahun_akademik_aktif = TahunAkademik.objects.get(aktif=True)
            context["tahun_akademik_aktif"] = tahun_akademik_aktif

            # PERUBAHAN: Menggunakan prefetch_related untuk ManyToManyField 'list_kelas'
            semua_jadwal = (
                Jadwal.objects.filter(tahun_akademik=tahun_akademik_aktif)
                .select_related("matakuliah", "dosen", "ruangan")
                .prefetch_related(
                    "list_kelas"  # Efisien untuk mengambil data dari ManyToMany
                )
            )

            if semua_jadwal.exists():
                context["jadwal_ditemukan"] = True

                # --- LOGIKA UNTUK TAMPILAN PER HARI ---

                # 1. Definisikan slot waktu dan hari
                slots = []
                current_time = time(7, 30)
                end_time = time(16, 0)
                interval = timedelta(minutes=30)
                base_date = datetime.now().date()

                while current_time <= end_time:
                    slots.append(current_time)
                    current_dt = datetime.combine(base_date, current_time)
                    current_time = (current_dt + interval).time()
                context["time_slots"] = slots

                hari_list = [
                    dict(Jadwal.HARI_CHOICES)[i] for i in range(5)
                ]  # Senin-Jumat
                all_rooms = list(Ruangan.objects.all().order_by("nama"))

                # 2. Siapkan grid kosong untuk setiap hari
                jadwal_per_hari = {}
                for hari in hari_list:
                    jadwal_per_hari[hari] = {
                        "rooms": all_rooms,
                        "timetable": {
                            slot.strftime("%H:%M"): {
                                room.id: {"jadwal": None, "spanned": False}
                                for room in all_rooms
                            }
                            for slot in slots
                        },
                    }

                # 3. Isi grid dengan data jadwal
                for jadwal in semua_jadwal.order_by(
                    "hari", "ruangan__nama", "jam_mulai"
                ):
                    hari_str = jadwal.get_hari_display()
                    if hari_str not in hari_list:
                        continue

                    # Hitung rowspan
                    start_dt = datetime.combine(base_date, jadwal.jam_mulai)
                    end_dt = datetime.combine(base_date, jadwal.jam_selesai)
                    duration = (end_dt - start_dt).total_seconds() / 60
                    rowspan = max(1, round(duration / 30))

                    # Cari slot waktu yang pas
                    placed = False
                    for slot in slots:
                        slot_dt = datetime.combine(base_date, slot)
                        if slot_dt >= start_dt and not placed:
                            slot_str = slot.strftime("%H:%M")

                            if (
                                jadwal_per_hari[hari_str]["timetable"][slot_str][
                                    jadwal.ruangan.id
                                ]["jadwal"]
                                is None
                            ):
                                timetable_cell = jadwal_per_hari[hari_str]["timetable"][
                                    slot_str
                                ][jadwal.ruangan.id]
                                timetable_cell["jadwal"] = jadwal
                                timetable_cell["rowspan"] = rowspan
                                placed = True

                                # Tandai sel-sel di bawahnya sebagai 'spanned'
                                for i in range(1, rowspan):
                                    next_slot_dt = slot_dt + (interval * i)
                                    if next_slot_dt.time() <= end_time:
                                        next_slot_str = next_slot_dt.time().strftime(
                                            "%H:%M"
                                        )
                                        jadwal_per_hari[hari_str]["timetable"][
                                            next_slot_str
                                        ][jadwal.ruangan.id]["spanned"] = True

                context["jadwal_per_hari"] = jadwal_per_hari

        except TahunAkademik.DoesNotExist:
            pass

        return render(request, self.template_name, context)
