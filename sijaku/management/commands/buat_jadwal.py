import random
from collections import defaultdict
from dataclasses import dataclass, field

from django.core.management.base import BaseCommand

# Pastikan nama aplikasi Anda benar ('sijaku' atau 'penjadwalan')
from sijaku.models import (
    Dosen,
    Jadwal,
    JadwalHarian,
    Kelas,
    MataKuliah,
    PemetaanDosenMK,
    Ruangan,
    TahunAkademik,
)
from sijaku.utils import (
    DURASI_PER_SKS,
    find_optimal_interval,
    generate_all_possible_slots,
    get_durasi_menit,
    get_time_blocks,
)


# === KELAS REPRESENTASI DATA BARU (Mendukung Kelas Gabungan) ===
@dataclass
class Gene:
    matakuliah: MataKuliah
    dosen: Dosen
    ruangan: Ruangan
    hari: int
    slot_waktu: tuple
    # Gene sekarang menampung BANYAK kelas
    list_kelas: list[Kelas] = field(default_factory=list)


class Chromosome:
    def __init__(self, genes: list[Gene]):
        self.genes = genes
        self.fitness = -1.0

    def __repr__(self):
        return f"Chromosome(fitness={self.fitness:.4f})"


# === KELAS UTAMA ALGORITMA GENETIKA ===
class GeneticAlgorithm:
    def __init__(
        self,
        population_size,
        crossover_rate,
        mutation_rate,
        tournament_size,
        generations,
    ):
        self.population_size = population_size
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.tournament_size = tournament_size
        self.generations = generations
        self.population = []
        self._load_data()

    def _load_data(self):
        try:
            self.tahun_akademik_aktif = TahunAkademik.objects.get(aktif=True)
        except TahunAkademik.DoesNotExist:
            raise Exception("Tidak ada Tahun Akademik yang aktif!")

        self.list_ruangan = list(Ruangan.objects.all())
        self.list_jadwal_harian = list(JadwalHarian.objects.all())
        all_pemetaan = list(
            PemetaanDosenMK.objects.filter(
                tahun_akademik=self.tahun_akademik_aktif
            ).select_related("matakuliah", "dosen_pengampu")
        )
        all_kelas = list(Kelas.objects.all())

        if (
            not all_pemetaan
            or not all_kelas
            or not self.list_ruangan
            or not self.list_jadwal_harian
        ):
            raise Exception(
                "Data dasar (pemetaan, kelas, ruangan, jadwal harian) tidak boleh kosong!"
            )

        print("Mengelompokkan data berdasarkan semester...")

        self.kelas_per_semester = defaultdict(list)
        tahun_akademik_mulai = int(self.tahun_akademik_aktif.tahun.split("/")[0])
        is_ganjil = self.tahun_akademik_aktif.semester == "ganjil"
        for kelas in all_kelas:
            selisih_tahun = tahun_akademik_mulai - kelas.tahun_angkatan
            semester_berjalan = (
                (selisih_tahun * 2) + 1 if is_ganjil else (selisih_tahun * 2) + 2
            )
            if 1 <= semester_berjalan <= 8:
                self.kelas_per_semester[semester_berjalan].append(kelas)

        self.acara_perkuliahan = []
        pemetaan_per_matakuliah = defaultdict(list)
        for pemetaan in all_pemetaan:
            pemetaan_per_matakuliah[pemetaan.matakuliah].append(pemetaan)

        for matakuliah, pemetaan_list in pemetaan_per_matakuliah.items():
            pemetaan = pemetaan_list[0]

            all_classes_in_semester = self.kelas_per_semester.get(
                matakuliah.semester, []
            )

            kelas_wajib_ambil = []
            for kelas in all_classes_in_semester:
                if matakuliah.peminatan is None:
                    kelas_wajib_ambil.append(kelas)
                elif matakuliah.peminatan == kelas.peminatan:
                    kelas_wajib_ambil.append(kelas)

            if kelas_wajib_ambil:
                self.acara_perkuliahan.append(
                    {"pemetaan": pemetaan, "kelas_wajib_ambil": kelas_wajib_ambil}
                )

        if not self.acara_perkuliahan:
            raise Exception("Tidak ada acara perkuliahan yang bisa dijadwalkan.")

        # --- LOGIKA BARU: Prioritaskan acara yang paling sulit (kelas paling banyak) ---
        self.acara_perkuliahan.sort(
            key=lambda x: len(x["kelas_wajib_ambil"]), reverse=True
        )

        print(
            f"Total acara perkuliahan yang akan dijadwalkan: {len(self.acara_perkuliahan)}"
        )

        all_matakuliah = [
            acara["pemetaan"].matakuliah for acara in self.acara_perkuliahan
        ]
        self.interval = find_optimal_interval(DURASI_PER_SKS)
        self.possible_slots = generate_all_possible_slots(
            self.list_jadwal_harian, all_matakuliah, self.interval
        )

    # --- FUNGSI BARU UNTUK MEMBUAT POPULASI AWAL ---
    def _create_initial_population(self):
        """Mencoba membuat satu kromosom sempurna, sisanya acak."""
        print("Membuat 1 kromosom 'sempurna' dengan metode deterministik...")

        perfect_chromosome = self._create_one_perfect_chromosome()
        if perfect_chromosome:
            print("Berhasil membuat 1 kromosom 'sempurna' sebagai benih.")
            self.population.append(perfect_chromosome)
        else:
            print("Gagal membuat kromosom sempurna, masalah mungkin over-constrained.")

        print(
            f"Membuat sisa populasi ({self.population_size - len(self.population)}) secara acak..."
        )
        while len(self.population) < self.population_size:
            genes = self._create_random_chromosome_genes()
            self.population.append(Chromosome(genes))

    def _create_one_perfect_chromosome(self):
        """Membuat satu jadwal bebas konflik secara deterministik."""
        genes = []
        temp_schedule = {"dosen": set(), "ruangan": set(), "kelas": set()}

        kelas_tersedia_per_acara = {
            acara["pemetaan"].matakuliah.id: list(acara["kelas_wajib_ambil"])
            for acara in self.acara_perkuliahan
        }

        for acara in self.acara_perkuliahan:
            matakuliah = acara["pemetaan"].matakuliah

            while kelas_tersedia_per_acara.get(matakuliah.id):
                # Cari penempatan terbaik untuk sesi berikutnya
                placed_gene = self._find_best_placement(
                    acara, kelas_tersedia_per_acara[matakuliah.id], temp_schedule
                )

                if not placed_gene:
                    # Gagal menemukan slot bebas konflik untuk acara ini, batalkan pembuatan
                    return None

                genes.append(placed_gene)

                # Perbarui jadwal sementara dan daftar kelas yang tersedia
                for block in get_time_blocks(
                    placed_gene.slot_waktu[0], placed_gene.slot_waktu[1], self.interval
                ):
                    temp_schedule["dosen"].add(
                        (placed_gene.dosen.id, placed_gene.hari, block)
                    )
                    temp_schedule["ruangan"].add(
                        (placed_gene.ruangan.id, placed_gene.hari, block)
                    )
                    for k in placed_gene.list_kelas:
                        temp_schedule["kelas"].add((k.id, placed_gene.hari, block))

                for k in placed_gene.list_kelas:
                    kelas_tersedia_per_acara[matakuliah.id].remove(k)

        return Chromosome(genes)

    def _find_best_placement(self, acara, kelas_tersedia, temp_schedule):
        """Mencari satu penempatan bebas konflik secara sistematis."""
        pemetaan = acara["pemetaan"]
        matakuliah = pemetaan.matakuliah
        durasi_key = f"{get_durasi_menit(matakuliah)}_menit"

        # Acak urutan agar tidak monoton
        shuffled_rooms = random.sample(self.list_ruangan, len(self.list_ruangan))

        for ruangan in shuffled_rooms:
            # Utamakan ruangan dengan kapasitas yang pas atau lebih besar
            kapasitas_ruangan = ruangan.kapasitas
            if kapasitas_ruangan < len(kelas_tersedia):
                kelas_untuk_sesi_ini = kelas_tersedia[:kapasitas_ruangan]
            else:
                kelas_untuk_sesi_ini = kelas_tersedia[:]

            # Cek tipe ruangan (teori di kelas biasa)
            if matakuliah.tipe == "teori" and ruangan.jenis != "kelas":
                continue

            for hari in self.possible_slots:
                for slot_waktu in self.possible_slots[hari].get(durasi_key, []):
                    # Cek apakah penempatan ini menimbulkan konflik
                    is_conflict = False
                    time_blocks = get_time_blocks(
                        slot_waktu[0], slot_waktu[1], self.interval
                    )
                    for block in time_blocks:
                        if (pemetaan.dosen_pengampu.id, hari, block) in temp_schedule[
                            "dosen"
                        ]:
                            is_conflict = True
                            break
                        if (ruangan.id, hari, block) in temp_schedule["ruangan"]:
                            is_conflict = True
                            break
                        for k in kelas_untuk_sesi_ini:
                            if (k.id, hari, block) in temp_schedule["kelas"]:
                                is_conflict = True
                                break
                        if is_conflict:
                            break

                    if not is_conflict:
                        # Ditemukan penempatan yang valid!
                        return Gene(
                            matakuliah=matakuliah,
                            dosen=pemetaan.dosen_pengampu,
                            ruangan=ruangan,
                            hari=hari,
                            slot_waktu=slot_waktu,
                            list_kelas=kelas_untuk_sesi_ini,
                        )
        return None  # Tidak ditemukan penempatan yang valid

    def _create_random_chromosome_genes(self):
        """Membuat satu kromosom secara acak (untuk sisa populasi)."""
        genes = []
        kelas_tersedia_per_semester = {
            sem: list(kelas) for sem, kelas in self.kelas_per_semester.items()
        }
        for acara in self.acara_perkuliahan:
            pemetaan = acara["pemetaan"]
            matakuliah = pemetaan.matakuliah
            semester = matakuliah.semester

            kelas_wajib_ambil_copy = list(acara["kelas_wajib_ambil"])

            while kelas_wajib_ambil_copy:
                ruangan = random.choice(self.list_ruangan)
                kapasitas_ruangan = ruangan.kapasitas

                kelas_untuk_sesi_ini = []
                for _ in range(kapasitas_ruangan):
                    if kelas_wajib_ambil_copy:
                        kelas_untuk_sesi_ini.append(kelas_wajib_ambil_copy.pop(0))

                if not kelas_untuk_sesi_ini:
                    break

                durasi_key = f"{get_durasi_menit(matakuliah)}_menit"
                hari = random.choice(list(self.possible_slots.keys()))
                slot_list = self.possible_slots[hari].get(durasi_key, [])
                while not slot_list:
                    hari = random.choice(list(self.possible_slots.keys()))
                    slot_list = self.possible_slots[hari].get(durasi_key, [])

                slot_waktu = random.choice(slot_list)

                genes.append(
                    Gene(
                        matakuliah=matakuliah,
                        dosen=pemetaan.dosen_pengampu,
                        ruangan=ruangan,
                        hari=hari,
                        slot_waktu=slot_waktu,
                        list_kelas=kelas_untuk_sesi_ini,
                    )
                )
        return genes

    def _calculate_fitness(self, chromosome):
        PENALTI_KERAS = 1000.0
        total_penalti = 0.0
        jadwal_dosen, jadwal_ruangan, jadwal_kelas = set(), set(), set()

        for gene in chromosome.genes:
            if not gene.dosen:
                total_penalti += PENALTI_KERAS
                continue
            time_blocks = get_time_blocks(
                gene.slot_waktu[0], gene.slot_waktu[1], self.interval
            )
            is_conflict = False
            for block in time_blocks:
                if (gene.dosen.id, gene.hari, block) in jadwal_dosen or (
                    gene.ruangan.id,
                    gene.hari,
                    block,
                ) in jadwal_ruangan:
                    total_penalti += PENALTI_KERAS
                    is_conflict = True
                    break
            if is_conflict:
                continue
            for kelas in gene.list_kelas:
                for block in time_blocks:
                    if (kelas.id, gene.hari, block) in jadwal_kelas:
                        total_penalti += PENALTI_KERAS
                        is_conflict = True
                        break
                if is_conflict:
                    break
            if is_conflict:
                continue
            for block in time_blocks:
                jadwal_dosen.add((gene.dosen.id, gene.hari, block))
                jadwal_ruangan.add((gene.ruangan.id, gene.hari, block))
                for kelas in gene.list_kelas:
                    jadwal_kelas.add((kelas.id, gene.hari, block))
            if gene.matakuliah.tipe == "teori" and gene.ruangan.jenis != "kelas":
                total_penalti += PENALTI_KERAS
        chromosome.fitness = 1.0 / (1.0 + total_penalti)

    def _selection(self):
        tournament = random.sample(self.population, self.tournament_size)
        return max(tournament, key=lambda c: c.fitness)

    def _crossover(self, parent1, parent2):
        if random.random() < self.crossover_rate:
            if len(parent1.genes) <= 1:
                return Chromosome(parent1.genes[:])
            point = random.randint(1, len(parent1.genes) - 1)
            child_genes = parent1.genes[:point] + parent2.genes[point:]
            return Chromosome(child_genes)
        return Chromosome(parent1.genes[:])

    def _mutate(self, chromosome):
        if not chromosome.genes or not self.list_ruangan:
            return
        if random.random() < self.mutation_rate:
            gene_to_mutate = random.choice(chromosome.genes)
            matakuliah = gene_to_mutate.matakuliah
            durasi_key = f"{get_durasi_menit(matakuliah)}_menit"
            hari = random.choice(list(self.possible_slots.keys()))
            slot_list = self.possible_slots[hari].get(durasi_key, [])
            while not slot_list:
                hari = random.choice(list(self.possible_slots.keys()))
                slot_list = self.possible_slots[hari].get(durasi_key, [])
            gene_to_mutate.hari = hari
            gene_to_mutate.slot_waktu = random.choice(slot_list)
            gene_to_mutate.ruangan = random.choice(self.list_ruangan)

    def run(self):
        self._create_initial_population()
        for generation in range(self.generations):
            for chromosome in self.population:
                self._calculate_fitness(chromosome)
            self.population.sort(key=lambda c: c.fitness, reverse=True)
            if generation % 10 == 0:
                print(
                    f"Generasi {generation}: Fitness Terbaik = {self.population[0].fitness:.4f}"
                )
            if self.population[0].fitness == 1.0:
                print("Solusi sempurna ditemukan!")
                break
            next_gen = self.population[:2]
            while len(next_gen) < self.population_size:
                p1 = self._selection()
                p2 = self._selection()
                child = self._crossover(p1, p2)
                self._mutate(child)
                next_gen.append(child)
            self.population = next_gen

    def get_best_chromosome(self):
        return self.population[0] if self.population else None


# === KELAS COMMAND UNTUK DJANGO ===
class Command(BaseCommand):
    help = "Membuat jadwal perkuliahan menggunakan Algoritma Genetika dengan logika kelas gabungan."

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Memulai proses penjadwalan..."))

        try:
            ga = GeneticAlgorithm(
                population_size=100,
                crossover_rate=0.9,
                mutation_rate=0.05,
                tournament_size=5,
                generations=200,  # Bisa dikurangi karena inisialisasi lebih baik
            )

            ga.run()
            best_chromosome = ga.get_best_chromosome()
            tahun_akademik_aktif = ga.tahun_akademik_aktif

            if best_chromosome and best_chromosome.fitness == 1.0:
                self.stdout.write(
                    self.style.SUCCESS(
                        "\nSolusi optimal ditemukan! Menyimpan jadwal ke database..."
                    )
                )
                Jadwal.objects.filter(tahun_akademik=tahun_akademik_aktif).delete()
                for gene in best_chromosome.genes:
                    jadwal_obj = Jadwal.objects.create(
                        tahun_akademik=tahun_akademik_aktif,
                        matakuliah=gene.matakuliah,
                        dosen=gene.dosen,
                        ruangan=gene.ruangan,
                        hari=gene.hari,
                        jam_mulai=gene.slot_waktu[0],
                        jam_selesai=gene.slot_waktu[1],
                    )
                    jadwal_obj.list_kelas.set(gene.list_kelas)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Berhasil menyimpan {len(best_chromosome.genes)} sesi jadwal baru!"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"\nTidak ditemukan solusi sempurna. Fitness terbaik: {best_chromosome.fitness if best_chromosome else 'N/A'}. Jadwal tidak disimpan."
                    )
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Terjadi error: {e}"))
