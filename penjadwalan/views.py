import queue
import threading

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_exempt

from data.models import Jabatan

# Thread-safe queue for progress updates
progress_queue = queue.Queue()
# Tambahkan 'stop_requested' untuk mengelola permintaan pembatalan
progress_state = {
    "running": False,
    "done": False,
    "result": None,
    "stop_requested": False,  # Flag untuk sinyal pembatalan
}


def is_wd1(user):
    return hasattr(user, "dosen") and user.dosen.jabatan.filter(nama="wd1").exists()


@login_required
@user_passes_test(is_wd1)
def genetika_wd1_view(request):
    # Saat halaman dimuat, pastikan status pembatalan direset
    progress_state["stop_requested"] = False
    return render(request, "penjadwalan/genetika_wd1.html")


@login_required
@user_passes_test(is_wd1)
def genetika_progress(request):
    def event_stream():
        while True:
            try:
                msg = progress_queue.get(timeout=1)
                yield f"data: {msg}\n\n".encode()
                if msg == "__DONE__":
                    break
            except queue.Empty:
                if progress_state["done"]:
                    break

    return StreamingHttpResponse(event_stream(), content_type="text/event-stream")


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
        return JsonResponse({"status": "invalid_params", "error": str(e)}, status=400)

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
            progress_queue.put("Error: Tahun akademik aktif tidak ditemukan.")
            progress_queue.put("__DONE__")
            progress_state["running"] = False
            progress_state["done"] = True
            progress_state["stop_requested"] = False
            return

        # Validasi pemetaan dosen harus ada dan status disetujui
        validasi = (
            ValidasiPemetaanDosenMK.objects.filter(tahun_akademik=tahun_akademik_aktif)
            .order_by("-id")
            .first()
        )
        if not validasi or validasi.status != "disetujui":
            progress_queue.put(
                "Error: Validasi pemetaan dosen untuk tahun akademik aktif belum disetujui."
            )
            progress_queue.put("__DONE__")
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
            progress_queue.put("Inisialisasi selesai. Data berhasil dimuat.")
            progress_queue.put(
                f"Total sesi yang akan dijadwalkan: {len(ga.genes_to_schedule)}"
            )
            ga._create_initial_population()
            progress_queue.put(
                f"Populasi awal sebanyak {len(ga.population)} individu berhasil dibuat."
            )

            if not ga.population:
                progress_queue.put(
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
                    progress_queue.put(
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
                    progress_queue.put(msg)

                if current_best.fitness > best_fitness_overall:
                    best_fitness_overall = current_best.fitness
                    no_improve_count = 0
                    ga.mutation_rate = ga.base_mutation_rate
                else:
                    no_improve_count += 1

                if no_improve_count > 30:
                    ga.mutation_rate = min(0.2, ga.mutation_rate * 1.2)

                hard_violations = ga._count_hard_constraint_violations(current_best)
                if no_improve_count > 100 and hard_violations == 0:
                    progress_queue.put(
                        "INFO: Proses dihentikan lebih awal (solusi stabil dan tanpa konflik)."
                    )
                    break

                if current_best.fitness == 1.0:
                    progress_queue.put("Solusi sempurna ditemukan!")
                    break

                # Repair minor conflict jika tidak ada peningkatan selama 50 generasi dan konflik < 5
                if (
                    no_improve_count > 50
                    and hard_violations > 0
                    and hard_violations < 5
                ):
                    progress_queue.put(
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
                hard_violations = ga._count_hard_constraint_violations(best_chromosome)
                if hard_violations > 0:
                    progress_queue.put(
                        f"Tidak disimpan: Jadwal masih memiliki {hard_violations} konflik hard constraint."
                    )
                else:
                    from penjadwalan.models import Jadwal

                    tahun_akademik_aktif = ga.tahun_akademik_aktif
                    # Hapus jadwal lama untuk tahun akademik aktif
                    Jadwal.objects.filter(tahun_akademik=tahun_akademik_aktif).delete()
                    jadwal_baru_list = [
                        Jadwal(
                            tahun_akademik=tahun_akademik_aktif,
                            matakuliah=gene.matakuliah,
                            dosen=gene.dosen,
                            kelas=gene.kelas,
                            ruangan=gene.ruangan,
                            hari=gene.hari,
                            jam_mulai=gene.slot_waktu[0],
                            jam_selesai=gene.slot_waktu[1],
                        )
                        for gene in best_chromosome.genes
                    ]
                    Jadwal.objects.bulk_create(jadwal_baru_list)
                    progress_queue.put(
                        f"Jadwal baru berhasil disimpan: {len(jadwal_baru_list)} sesi."
                    )
            else:
                progress_queue.put("Tidak ada solusi jadwal yang dapat disimpan.")
            progress_queue.put(f"Selesai. Fitness terbaik: {progress_state['result']}")

        except Exception as e:
            progress_queue.put(f"Error: {e}")
        finally:
            progress_queue.put("__DONE__")
            progress_state["running"] = False
            progress_state["done"] = True
            progress_state["stop_requested"] = False  # Reset flag untuk run berikutnya

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
    from penjadwalan.models import Jadwal

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
            jadwal_list, key=lambda j: (j.hari, j.matakuliah.nama.lower(), j.jam_mulai)
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

    tanggal_cetak_str = request.GET.get("tanggal_cetak", "")
    tanggal_obj = parse_date(tanggal_cetak_str)
    if tanggal_obj:
        tanggal_cetak_long = tanggal_obj.strftime("%d %B %Y")
    else:
        tanggal_cetak_long = ""

    return render(
        request,
        "penjadwalan/print_jadwal.html",
        {
            "tahun_akademik": tahun_akademik_aktif,
            "jadwal_per_semester": jadwal_per_semester,
            "wd1": wd1,
            "tanggal_cetak": tanggal_cetak_str,
            "tanggal_cetak_long": tanggal_cetak_long,
            "tanggal": tanggal_obj,
        },
    )
