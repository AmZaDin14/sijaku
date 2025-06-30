import threading

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_exempt

from data.models import Jabatan

from .models import JadwalGenetika

# Tambahkan 'stop_requested' untuk mengelola permintaan pembatalan
progress_state = {
    "running": False,
    "done": False,
    "result": None,
    "stop_requested": False,  # Flag untuk sinyal pembatalan
}

channel_layer = get_channel_layer()


def send_ws_message(message):
    """
    Kirim pesan ke WebSocket channel layer.
    """
    async_to_sync(channel_layer.group_send)(
        "genetika_progress",  # Ganti dengan nama grup yang sesuai
        {
            "type": "send_progress",
            "message": message,
        },
    )


def is_wd1(user):
    return (
        hasattr(user, "dosen")
        and user.dosen.jabatan.filter(nama="wd1").exists()
    )


@login_required
@user_passes_test(is_wd1)
def genetika_wd1_view(request):
    # Saat halaman dimuat, pastikan status pembatalan direset
    progress_state["stop_requested"] = False
    return render(request, "penjadwalan/genetika_wd1.html")


@login_required
@user_passes_test(is_wd1)
@csrf_exempt
def genetika_start(request):
    if progress_state["running"]:
        return JsonResponse({"status": "already_running"})

    # Ambil parameter dari request body (JSON)
    import json

    try:
        params = json.loads(request.body.decode())
        population_size = int(params.get("population_size", 100))
        crossover_rate = float(params.get("crossover_rate", 0.9))
        mutation_rate = float(params.get("mutation_rate", 0.02))
        tournament_size = int(params.get("tournament_size", 5))
        generations = int(params.get("generations", 500))
        menit_per_sks = int(params.get("menit_per_sks", 30))
    except Exception as e:
        return JsonResponse(
            {"status": "invalid_params", "error": str(e)}, status=400
        )

    def run_genetika():
        from data import utils as data_utils
        from data.management.commands.buat_jadwal import GeneticAlgorithm
        from data.models import (
            TahunAkademik,
            ValidasiPemetaanDosenMK,  # perbaiki nama model
        )

        progress_state["running"] = True
        progress_state["done"] = False
        progress_state["result"] = None
        progress_state["stop_requested"] = False

        # Ambil tahun akademik aktif
        tahun_akademik_aktif = TahunAkademik.objects.filter(aktif=True).first()
        if not tahun_akademik_aktif:
            send_ws_message("Error: Tahun akademik aktif tidak ditemukan.")
            send_ws_message("__DONE__")
            progress_state["running"] = False
            progress_state["done"] = True
            progress_state["stop_requested"] = False
            return

        # Validasi pemetaan dosen harus ada dan status disetujui
        validasi = (
            ValidasiPemetaanDosenMK.objects.filter(
                tahun_akademik=tahun_akademik_aktif
            )
            .order_by("-id")
            .first()
        )
        if not validasi or validasi.status != "disetujui":
            send_ws_message(
                "Error: Validasi pemetaan dosen untuk tahun akademik aktif belum disetujui."
            )
            send_ws_message("__DONE__")
            progress_state["running"] = False
            progress_state["done"] = True
            progress_state["stop_requested"] = False
            return

        # Set DURASI_PER_SKS secara dinamis
        data_utils.DURASI_PER_SKS = menit_per_sks

        try:
            ga = GeneticAlgorithm(
                population_size=population_size,
                crossover_rate=crossover_rate,
                mutation_rate=mutation_rate,
                tournament_size=tournament_size,
                generations=generations,
            )
            send_ws_message("Inisialisasi selesai. Data berhasil dimuat.")
            send_ws_message(
                f"Total sesi yang akan dijadwalkan: {len(ga.genes_to_schedule)}"
            )
            ga._create_initial_population()
            send_ws_message(
                f"Populasi awal sebanyak {len(ga.population)} individu berhasil dibuat."
            )

            if not ga.population:
                send_ws_message(
                    "Error: Gagal membuat populasi awal. Proses dihentikan."
                )
                raise ValueError(
                    "Populasi awal kosong setelah _create_initial_population."
                )

            best_fitness_overall = -1.0
            no_improve_count = 0

            for generation in range(ga.generations):
                # === PEMERIKSAAN PEMBATALAN ===
                # Di setiap awal generasi, periksa apakah ada permintaan untuk berhenti.
                if progress_state.get("stop_requested", False):
                    send_ws_message(
                        "INFO: Proses pembatalan diterima. Menghentikan evolusi..."
                    )
                    break  # Keluar dari loop generasi
                # === AKHIR PEMERIKSAAN ===

                for chromosome in ga.population:
                    ga._calculate_fitness(chromosome)

                ga.population.sort(key=lambda c: c.fitness, reverse=True)
                current_best = ga.population[0]

                if (generation % 10 == 0) or (generation == ga.generations - 1):
                    avg_fitness = sum(c.fitness for c in ga.population) / len(
                        ga.population
                    )
                    msg = f"Generasi {generation}: Fitness Terbaik={current_best.fitness:.4f}, Rata-rata={avg_fitness:.4f}"
                    send_ws_message(msg)

                if current_best.fitness > best_fitness_overall:
                    best_fitness_overall = current_best.fitness
                    no_improve_count = 0
                    ga.mutation_rate = ga.base_mutation_rate
                else:
                    no_improve_count += 1

                if no_improve_count > 30:
                    ga.mutation_rate = min(0.2, ga.mutation_rate * 1.2)

                hard_violations = ga._count_hard_constraint_violations(
                    current_best
                )
                if no_improve_count > 100 and hard_violations == 0:
                    send_ws_message(
                        "INFO: Proses dihentikan lebih awal (solusi stabil dan tanpa konflik)."
                    )
                    break

                if current_best.fitness == 1.0:
                    send_ws_message("Solusi sempurna ditemukan!")
                    break

                # Repair minor conflict jika tidak ada peningkatan selama 50 generasi dan konflik < 5
                if (
                    no_improve_count > 50
                    and hard_violations > 0
                    and hard_violations < 5
                ):
                    send_ws_message(
                        f"INFO: Repair minor conflict pada solusi terbaik di generasi {generation}..."
                    )
                    ga._repair_minor_conflicts(current_best)
                    ga._calculate_fitness(current_best)
                    ga.population[0] = current_best

                next_gen = ga.population[:2]
                while len(next_gen) < ga.population_size:
                    p1 = ga._selection()
                    p2 = ga._selection()
                    child = ga._crossover(p1, p2)
                    ga._mutate(child)
                    next_gen.append(child)
                ga.population = next_gen

            best_chromosome = ga.get_best_chromosome()
            progress_state["result"] = (
                best_chromosome.fitness if best_chromosome else None
            )
            # === SIMPAN JADWAL KE DATABASE ===
            if best_chromosome:
                hard_violations = ga._count_hard_constraint_violations(
                    best_chromosome
                )
                if hard_violations > 0:
                    send_ws_message(
                        f"Tidak disimpan: Jadwal masih memiliki {hard_violations} konflik hard constraint."
                    )
                else:
                    tahun_akademik_aktif = ga.tahun_akademik_aktif
                    # Simpan ke histori JadwalGenetika
                    JadwalGenetika.objects.create(
                        tahun_akademik=tahun_akademik_aktif,
                        parameter={
                            "population_size": population_size,
                            "crossover_rate": crossover_rate,
                            "mutation_rate": mutation_rate,
                            "tournament_size": tournament_size,
                            "generations": generations,
                            "menit_per_sks": menit_per_sks,
                        },
                        hasil_jadwal=[
                            {
                                "matakuliah": gene.matakuliah.id,
                                "dosen": gene.dosen.id,
                                "kelas": gene.kelas.id,
                                "ruangan": gene.ruangan.id,
                                "hari": gene.hari,
                                "jam_mulai": str(gene.slot_waktu[0]),
                                "jam_selesai": str(gene.slot_waktu[1]),
                            }
                            for gene in best_chromosome.genes
                        ],
                        status="draft",
                    )
                    send_ws_message("Jadwal baru berhasil disimpan ke histori")
            else:
                send_ws_message("Tidak ada solusi jadwal yang dapat disimpan.")
            send_ws_message(
                f"Selesai. Fitness terbaik: {progress_state['result']}"
            )

        except Exception as e:
            send_ws_message(f"Error: {e}")
        finally:
            send_ws_message("__DONE__")
            progress_state["running"] = False
            progress_state["done"] = True
            progress_state["stop_requested"] = (
                False  # Reset flag untuk run berikutnya
            )

    threading.Thread(target=run_genetika, daemon=True).start()
    return JsonResponse({"status": "started"})


# === VIEW BARU UNTUK MEMBATALKAN PROSES ===
@login_required
@user_passes_test(is_wd1)
@csrf_exempt
def genetika_cancel(request):
    if request.method == "POST":
        if progress_state["running"]:
            progress_state["stop_requested"] = True
            return JsonResponse({"status": "cancel_requested"})
        else:
            return JsonResponse({"status": "not_running"})
    return JsonResponse({"status": "invalid_method"}, status=405)


@login_required
def print_jadwal_per_semester(request):
    from data.models import TahunAkademik
    from penjadwalan.models import Jadwal, JadwalGenetika

    tahun_akademik_aktif = TahunAkademik.objects.filter(aktif=True).first()
    if not tahun_akademik_aktif:
        return render(
            request,
            "penjadwalan/print_jadwal.html",
            {"error": "Tahun akademik aktif tidak ditemukan."},
        )

    # Ambil semua jadwal untuk tahun akademik aktif
    jadwal_qs = Jadwal.objects.filter(
        tahun_akademik=tahun_akademik_aktif
    ).select_related("matakuliah", "dosen", "kelas", "ruangan")
    # Kelompokkan berdasarkan semester mata kuliah
    jadwal_per_semester = {}
    for jadwal in jadwal_qs:
        semester = jadwal.matakuliah.semester
        if semester not in jadwal_per_semester:
            jadwal_per_semester[semester] = []
        jadwal_per_semester[semester].append(jadwal)
    # Urutkan berdasarkan semester
    jadwal_per_semester = dict(sorted(jadwal_per_semester.items()))
    # Urutkan setiap semester: hari, matakuliah.nama, jam_mulai
    for semester, jadwal_list in jadwal_per_semester.items():
        jadwal_per_semester[semester] = sorted(
            jadwal_list,
            key=lambda j: (j.hari, j.matakuliah.nama.lower(), j.jam_mulai),
        )

    wd1 = Jabatan.objects.filter(nama="wd1").first().dosen

    import locale

    # Set locale ke Indonesia (jika tersedia di sistem)
    try:
        locale.setlocale(locale.LC_TIME, "id_ID.UTF-8")
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, "id_ID")
        except locale.Error:
            locale.setlocale(locale.LC_TIME, "")  # fallback ke default

    # Ambil tanggal publikasi dari JadwalGenetika yang status publish
    jadwal_genetika_publish = JadwalGenetika.objects.filter(
        tahun_akademik=tahun_akademik_aktif, status="publish"
    ).order_by("-tanggal_publikasi").first()
    if jadwal_genetika_publish and jadwal_genetika_publish.tanggal_publikasi:
        tanggal_cetak_obj = jadwal_genetika_publish.tanggal_publikasi
        tanggal_cetak_str = tanggal_cetak_obj.strftime("%Y-%m-%d")
        tanggal_cetak_long = tanggal_cetak_obj.strftime("%d %B %Y")
    else:
        tanggal_cetak_str = ""
        tanggal_cetak_long = ""
        tanggal_cetak_obj = None

    return render(
        request,
        "penjadwalan/print_jadwal.html",
        {
            "tahun_akademik": tahun_akademik_aktif,
            "jadwal_per_semester": jadwal_per_semester,
            "wd1": wd1,
            "tanggal_cetak": tanggal_cetak_str,
            "tanggal_cetak_long": tanggal_cetak_long,
            "tanggal": tanggal_cetak_obj,
        },
    )


@login_required
@user_passes_test(is_wd1)
def jadwal_genetika_list(request):
    from data.models import TahunAkademik

    ta = TahunAkademik.objects.filter(aktif=True).first()
    hasil_list = []
    if ta:
        hasil_list = JadwalGenetika.objects.filter(tahun_akademik=ta).order_by(
            "-waktu_dibuat"
        )
    return render(
        request,
        "penjadwalan/jadwal_genetika_list.html",
        {"tahun_akademik": ta, "hasil_list": hasil_list},
    )


@login_required
@user_passes_test(is_wd1)
def jadwal_genetika_detail(request, pk):
    hasil = JadwalGenetika.objects.get(pk=pk)
    from data.models import Dosen, Kelas, MataKuliah, Ruangan
    from penjadwalan.models import JadwalHarian

    HARI_MAP = dict(JadwalHarian.HARI_CHOICES)

    jadwal_list = []
    for item in hasil.hasil_jadwal:
        mk = MataKuliah.objects.filter(id=item.get("matakuliah")).first()
        dosen = Dosen.objects.filter(id=item.get("dosen")).first()
        kelas = Kelas.objects.filter(id=item.get("kelas")).first()
        ruangan = Ruangan.objects.filter(id=item.get("ruangan")).first()
        hari_label = HARI_MAP.get(item.get("hari"), item.get("hari"))
        jadwal_list.append(
            {
                **item,
                "matakuliah_nama": mk.nama if mk else item.get("matakuliah"),
                "dosen_nama": dosen.nama if dosen else item.get("dosen"),
                "kelas_nama": kelas.nama if kelas else item.get("kelas"),
                "ruangan_nama": ruangan.nama
                if ruangan
                else item.get("ruangan"),
                "hari_label": hari_label,
            }
        )
    # Urutkan berdasarkan hari, lalu nama matakuliah, lalu jam_mulai
    jadwal_list = sorted(
        jadwal_list,
        key=lambda x: (
            x.get("hari", 0),
            str(x.get("matakuliah_nama", "")).lower(),
            x.get("jam_mulai", ""),
        ),
    )
    return render(
        request,
        "penjadwalan/jadwal_genetika_detail.html",
        {"hasil": hasil, "jadwal_list": jadwal_list},
    )


@login_required
@user_passes_test(is_wd1)
@csrf_exempt
def jadwal_genetika_publish(request, pk):
    import json
    from django.utils import timezone
    from penjadwalan.models import Jadwal

    if request.method != "POST":
        return JsonResponse({"status": "invalid_method"}, status=405)
    hasil = JadwalGenetika.objects.get(pk=pk)
    ta = hasil.tahun_akademik
    try:
        data = json.loads(request.body.decode())
        tanggal_publikasi = data.get("tanggal_publikasi")
    except Exception:
        tanggal_publikasi = None
    if not tanggal_publikasi:
        tanggal_publikasi = timezone.now().date()

    # Jika status draft, lakukan publish penuh (hapus dan insert jadwal)
    if hasil.status == "draft":
        Jadwal.objects.filter(tahun_akademik=ta).delete()
        for item in hasil.hasil_jadwal:
            Jadwal.objects.create(
                tahun_akademik=ta,
                matakuliah_id=item.get("matakuliah"),
                dosen_id=item.get("dosen"),
                kelas_id=item.get("kelas"),
                ruangan_id=item.get("ruangan"),
                hari=item.get("hari"),
                jam_mulai=item.get("jam_mulai"),
                jam_selesai=item.get("jam_selesai"),
            )
        # Set semua hasil lain draft dan tanggal_publikasi null
        JadwalGenetika.objects.filter(tahun_akademik=ta).exclude(pk=pk).update(
            status="draft", tanggal_publikasi=None
        )
        hasil.status = "publish"
    # Jika sudah publish, hanya update tanggal_publikasi
    hasil.tanggal_publikasi = tanggal_publikasi
    hasil.save()
    return JsonResponse({"status": "ok"})
