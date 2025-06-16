import random
from collections import defaultdict
from dataclasses import dataclass

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


# === KELAS UNTUK REPRESENTASI DATA ===
@dataclass
class Gene:
    matakuliah: MataKuliah
    dosen: Dosen
    ruangan: Ruangan
    hari: int
    slot_waktu: tuple
    kelas: Kelas


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

        # Load data dasar sekali saja
        self.list_ruangan = list(Ruangan.objects.all())
        self.list_kelas = list(Kelas.objects.all())
        self.list_jadwal_harian = list(JadwalHarian.objects.all())
        all_pemetaan = list(
            PemetaanDosenMK.objects.filter(
                tahun_akademik=self.tahun_akademik_aktif
            ).select_related("matakuliah", "dosen_pengampu")
        )

        if (
            not all_pemetaan
            or not self.list_kelas
            or not self.list_ruangan
            or not self.list_jadwal_harian
        ):
            raise Exception(
                "Data dasar (pemetaan, kelas, ruangan, jadwal harian) tidak boleh kosong!"
            )

        self.genes_to_schedule = []
        print(
            "Membangun daftar tugas penjadwalan berdasarkan Pemetaan Dosen-MK yang aktif..."
        )

        tahun_akademik_mulai = int(self.tahun_akademik_aktif.tahun.split("/")[0])
        is_ganjil = self.tahun_akademik_aktif.semester == "ganjil"

        for pemetaan in all_pemetaan:
            matakuliah = pemetaan.matakuliah
            for kelas in self.list_kelas:
                selisih_tahun = tahun_akademik_mulai - kelas.tahun_angkatan
                semester_berjalan = (
                    (selisih_tahun * 2) + 1 if is_ganjil else (selisih_tahun * 2) + 2
                )
                if matakuliah.semester == semester_berjalan and (
                    matakuliah.peminatan is None
                    or matakuliah.peminatan == kelas.peminatan
                ):
                    self.genes_to_schedule.append((pemetaan, kelas))

        if not self.genes_to_schedule:
            raise Exception(
                "Tidak ada kombinasi (Mata Kuliah, Kelas) yang bisa dijadwalkan. Periksa data semester berjalan dan pemetaan."
            )

        print(f"Total sesi yang akan dijadwalkan: {len(self.genes_to_schedule)}")

        matakuliah_yang_dijadwalkan = [p.matakuliah for p, k in self.genes_to_schedule]
        self.interval = find_optimal_interval(DURASI_PER_SKS)
        self.possible_slots = generate_all_possible_slots(
            self.list_jadwal_harian, matakuliah_yang_dijadwalkan, self.interval
        )

    # Fungsi ini tetap dipakai untuk mutasi
    def _create_random_gene(self, pemetaan, kelas):
        matakuliah = pemetaan.matakuliah
        durasi_key = f"{get_durasi_menit(matakuliah)}_menit"
        hari = random.choice(list(self.possible_slots.keys()))
        slot_list = self.possible_slots[hari].get(durasi_key, [])
        while not slot_list:
            hari = random.choice(list(self.possible_slots.keys()))
            slot_list = self.possible_slots[hari].get(durasi_key, [])

        slot_waktu = random.choice(slot_list)
        ruangan = random.choice(self.list_ruangan)
        return Gene(
            matakuliah, pemetaan.dosen_pengampu, ruangan, hari, slot_waktu, kelas
        )

    # === LOGIKA BARU: MEMBUAT POPULASI AWAL YANG LEBIH CERDAS ===
    def _create_initial_population(self):
        """Membuat populasi awal dengan metode Greedy Random."""
        print("Membuat populasi awal yang lebih cerdas (Greedy Random)...")
        for _ in range(self.population_size):
            genes = []

            # Buat "papan catur" sementara untuk melacak konflik saat membangun satu kromosom
            temp_schedule = {"dosen": set(), "ruangan": set(), "kelas": set()}

            for pemetaan, kelas in self.genes_to_schedule:
                best_gene_candidate = None
                lowest_conflict_score = float("inf")

                # Coba 10 penempatan acak dan pilih yang terbaik
                for _ in range(10):
                    candidate_gene = self._create_random_gene(pemetaan, kelas)

                    # Hitung konflik yang akan ditimbulkan oleh gen kandidat ini
                    conflicts = 0
                    time_blocks = get_time_blocks(
                        candidate_gene.slot_waktu[0],
                        candidate_gene.slot_waktu[1],
                        self.interval,
                    )
                    for block in time_blocks:
                        if (
                            candidate_gene.dosen.id,
                            candidate_gene.hari,
                            block,
                        ) in temp_schedule["dosen"]:
                            conflicts += 1
                        if (
                            candidate_gene.ruangan.id,
                            candidate_gene.hari,
                            block,
                        ) in temp_schedule["ruangan"]:
                            conflicts += 1
                        if (
                            candidate_gene.kelas.id,
                            candidate_gene.hari,
                            block,
                        ) in temp_schedule["kelas"]:
                            conflicts += 1

                    if conflicts < lowest_conflict_score:
                        lowest_conflict_score = conflicts
                        best_gene_candidate = candidate_gene

                    # Jika sudah menemukan yang tanpa konflik, langsung pakai
                    if lowest_conflict_score == 0:
                        break

                # Tambahkan gen terbaik yang ditemukan ke dalam daftar
                genes.append(best_gene_candidate)

                # Perbarui "papan catur" sementara dengan gen yang baru ditempatkan
                final_time_blocks = get_time_blocks(
                    best_gene_candidate.slot_waktu[0],
                    best_gene_candidate.slot_waktu[1],
                    self.interval,
                )
                for block in final_time_blocks:
                    temp_schedule["dosen"].add(
                        (best_gene_candidate.dosen.id, best_gene_candidate.hari, block)
                    )
                    temp_schedule["ruangan"].add(
                        (
                            best_gene_candidate.ruangan.id,
                            best_gene_candidate.hari,
                            block,
                        )
                    )
                    temp_schedule["kelas"].add(
                        (best_gene_candidate.kelas.id, best_gene_candidate.hari, block)
                    )

            self.population.append(Chromosome(genes))

    def _calculate_fitness(self, chromosome):
        PENALTI_KERAS = 1000.0
        PENALTI_PREFERENSI_RUANG = 10.0
        PENALTI_LUNAK = 1.0

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
                key_dosen = (gene.dosen.id, gene.hari, block)
                key_ruangan = (gene.ruangan.id, gene.hari, block)
                key_kelas = (gene.kelas.id, gene.hari, block)
                if (
                    key_dosen in jadwal_dosen
                    or key_ruangan in jadwal_ruangan
                    or key_kelas in jadwal_kelas
                ):
                    total_penalti += PENALTI_KERAS
                    is_conflict = True
                    break
            if is_conflict:
                continue

            for block in time_blocks:
                jadwal_dosen.add((gene.dosen.id, gene.hari, block))
                jadwal_ruangan.add((gene.ruangan.id, gene.hari, block))
                jadwal_kelas.add((gene.kelas.id, gene.hari, block))

            if gene.matakuliah.tipe == "praktik" and gene.ruangan.jenis != "lab":
                total_penalti += PENALTI_PREFERENSI_RUANG
            if gene.matakuliah.tipe == "teori" and gene.ruangan.jenis != "kelas":
                total_penalti += PENALTI_KERAS

        chromosome.fitness = 1.0 / (1.0 + total_penalti)

    # === FUNGSI DEBUGGING (TETAP ADA JIKA DIPERLUKAN) ===
    def _debug_chromosome(self, chromosome):
        # (Kode debug tidak berubah, tetap bisa digunakan)
        print("\n--- MEMULAI DEBUGGING UNTUK KROMOSOM TERBURUK ---")
        HARI_MAP = {
            0: "Senin",
            1: "Selasa",
            2: "Rabu",
            3: "Kamis",
            4: "Jumat",
            5: "Sabtu",
            6: "Minggu",
        }
        jadwal_dosen, jadwal_ruangan, jadwal_kelas = {}, {}, {}
        konflik_count = 0
        for i, gene in enumerate(chromosome.genes):
            hari_str = HARI_MAP.get(gene.hari, "HARI_TIDAK_DIKETAHUI")
            dosen_nama = gene.dosen.nama if gene.dosen else "TANPA DOSEN"
            if gene.matakuliah.tipe == "teori" and gene.ruangan.jenis != "kelas":
                print(
                    f"-> KONFLIK TIPE RUANG: Matkul Teori '{gene.matakuliah.nama}' ditempatkan di Lab '{gene.ruangan.nama}'"
                )
                konflik_count += 1
            time_blocks = get_time_blocks(
                gene.slot_waktu[0], gene.slot_waktu[1], self.interval
            )
            for block in time_blocks:
                key_dosen = (gene.dosen.id, gene.hari, block)
                if key_dosen in jadwal_dosen:
                    gene_konflik = jadwal_dosen[key_dosen]
                    print(
                        f"-> KONFLIK DOSEN: '{dosen_nama}' di hari {hari_str} jam {block}."
                    )
                    print(
                        f"   - Bertabrakan: Matkul '{gene.matakuliah.nama}' untuk Kelas {gene.kelas}"
                    )
                    print(
                        f"   - Dengan: Matkul '{gene_konflik.matakuliah.nama}' untuk Kelas {gene_konflik.kelas}"
                    )
                    konflik_count += 1
                else:
                    jadwal_dosen[key_dosen] = gene
                key_ruangan = (gene.ruangan.id, gene.hari, block)
                if key_ruangan in jadwal_ruangan:
                    gene_konflik = jadwal_ruangan[key_ruangan]
                    print(
                        f"-> KONFLIK RUANGAN: '{gene.ruangan.nama}' di hari {hari_str} jam {block}."
                    )
                    print(
                        f"   - Bertabrakan: Matkul '{gene.matakuliah.nama}' untuk Kelas {gene.kelas}"
                    )
                    print(
                        f"   - Dengan: Matkul '{gene_konflik.matakuliah.nama}' untuk Kelas {gene_konflik.kelas}"
                    )
                    konflik_count += 1
                else:
                    jadwal_ruangan[key_ruangan] = gene
                key_kelas = (gene.kelas.id, gene.hari, block)
                if key_kelas in jadwal_kelas:
                    gene_konflik = jadwal_kelas[key_kelas]
                    print(
                        f"-> KONFLIK KELAS: '{gene.kelas}' di hari {hari_str} jam {block}."
                    )
                    print(f"   - Bertabrakan: Matkul '{gene.matakuliah.nama}'")
                    print(f"   - Dengan: Matkul '{gene_konflik.matakuliah.nama}'")
                    konflik_count += 1
                else:
                    jadwal_kelas[key_kelas] = gene
        print(f"--- DEBUG SELESAI: Total {konflik_count} konflik terdeteksi. ---")

    def _selection(self):
        tournament = random.sample(self.population, self.tournament_size)
        return max(tournament, key=lambda c: c.fitness)

    def _crossover(self, parent1, parent2):
        if random.random() < self.crossover_rate:
            if not self.genes_to_schedule or len(self.genes_to_schedule) <= 1:
                return Chromosome(parent1.genes[:])
            point = random.randint(1, len(self.genes_to_schedule) - 1)
            child_genes = parent1.genes[:point] + parent2.genes[point:]
            return Chromosome(child_genes)
        return Chromosome(parent1.genes[:])

    def _mutate(self, chromosome):
        if not self.genes_to_schedule:
            return
        for i in range(len(chromosome.genes)):
            if random.random() < self.mutation_rate:
                gene_info = self.genes_to_schedule[i]
                chromosome.genes[i] = self._create_random_gene(
                    gene_info[0], gene_info[1]
                )

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
    help = "Membuat jadwal perkuliahan menggunakan Algoritma Genetika"

    def add_arguments(self, parser):
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Jalankan dalam mode debug untuk menganalisis konflik pada satu jadwal.",
        )

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Memulai proses penjadwalan..."))

        is_debug_mode = kwargs["debug"]

        try:
            generations = 1 if is_debug_mode else 500

            ga = GeneticAlgorithm(
                population_size=100,
                crossover_rate=0.9,
                mutation_rate=0.02,
                tournament_size=5,
                generations=generations,
            )

            ga.run()

            if is_debug_mode:
                worst_chromosome = ga.population[-1]
                ga._debug_chromosome(worst_chromosome)
                return

            best_chromosome = ga.get_best_chromosome()
            tahun_akademik_aktif = ga.tahun_akademik_aktif

            if best_chromosome:
                if best_chromosome.fitness == 1.0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            "\nSolusi optimal ditemukan! Menyimpan jadwal ke database..."
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"\nSolusi tidak sempurna ditemukan. Menyimpan jadwal dengan fitness terbaik ({best_chromosome.fitness})."
                        )
                    )
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
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Berhasil menyimpan {len(jadwal_baru_list)} sesi jadwal baru!"
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
