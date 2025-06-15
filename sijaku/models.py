from django.db import models


class Dosen(models.Model):
    nidn = models.CharField(max_length=20, unique=True)
    nama = models.CharField(max_length=100)

    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dosen",
    )

    def __str__(self):
        return self.nama

    class Meta:
        verbose_name = "Dosen"
        verbose_name_plural = "Dosen"
        ordering = ["nama"]


class Jabatan(models.Model):
    JABATAN_CHOICES = [
        ("kaprodi", "Kaprodi"),
        ("wd1", "WD1"),
    ]
    nama = models.CharField(max_length=20, choices=JABATAN_CHOICES, unique=True)
    dosen = models.ForeignKey(
        "Dosen",
        on_delete=models.SET_NULL,
        related_name="jabatan",
        null=True,
        blank=True,
    )

    def __str__(self):
        return dict(self.JABATAN_CHOICES).get(self.nama, self.nama)

    class Meta:
        verbose_name = "Jabatan"
        verbose_name_plural = "Jabatan"
        ordering = ["nama"]
        unique_together = ("nama",)


class Peminatan(models.Model):
    kode = models.CharField(max_length=10, unique=True)
    nama = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.nama}"

    class Meta:
        verbose_name = "Peminatan"
        verbose_name_plural = "Peminatan"
        ordering = ["kode"]


class MataKuliah(models.Model):
    TIPE_CHOICES = [
        ("teori", "Teori"),
        ("praktik", "Praktik"),
    ]
    kode = models.CharField(max_length=10, unique=True)
    nama = models.CharField(max_length=100)
    sks = models.PositiveIntegerField()
    semester = models.PositiveSmallIntegerField(default=1)
    tipe = models.CharField(max_length=10, choices=TIPE_CHOICES, default="teori")
    peminatan = models.ForeignKey(
        "Peminatan",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="matakuliah",
    )

    def __str__(self):
        return f"{self.nama}"

    class Meta:
        verbose_name = "Mata Kuliah"
        verbose_name_plural = "Mata Kuliah"
        ordering = ["semester", "kode"]


class TahunAkademik(models.Model):
    SEMESTER_CHOICES = [
        ("ganjil", "Ganjil"),
        ("genap", "Genap"),
    ]

    tahun = models.CharField(max_length=9)
    semester = models.CharField(
        max_length=10, choices=SEMESTER_CHOICES, default="ganjil"
    )
    aktif = models.BooleanField(default=False)

    def __str__(self):
        return self.tahun

    class Meta:
        verbose_name = "Tahun Akademik"
        verbose_name_plural = "Tahun Akademik"
        ordering = ["-tahun"]
        unique_together = ("tahun", "semester")


class Ruangan(models.Model):
    JENIS_CHOICES = [
        ("kelas", "Ruang Kelas"),
        ("lab", "Lab Komputer"),
    ]
    nama = models.CharField(max_length=50, unique=True)
    jenis = models.CharField(max_length=10, choices=JENIS_CHOICES)
    kapasitas = models.PositiveIntegerField(
        help_text="Jumlah kelas yang dapat ditampung"
    )

    def __str__(self):
        jenis_display = dict(self.JENIS_CHOICES).get(self.jenis, self.jenis)
        return f"{self.nama} ({jenis_display})"

    class Meta:
        verbose_name = "Ruangan"
        verbose_name_plural = "Ruangan"
        ordering = ["nama"]


class PemetaanDosenMK(models.Model):
    tahun_akademik = models.ForeignKey(
        TahunAkademik, on_delete=models.CASCADE, related_name="penyelenggaraan"
    )
    matakuliah = models.ForeignKey(
        MataKuliah, on_delete=models.CASCADE, related_name="penyelenggaraan"
    )
    dosen_pengampu = models.ForeignKey(
        Dosen,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pengampu_matakuliah",
    )

    class Meta:
        verbose_name = "Pemetaan Dosen-MK"
        verbose_name_plural = "Pemetaan Dosen-MK"
        unique_together = ("tahun_akademik", "matakuliah")
        ordering = ["tahun_akademik", "matakuliah"]

    def __str__(self):
        return f"{self.matakuliah} ({self.tahun_akademik})"


class Kelas(models.Model):
    tahun_angkatan = models.PositiveIntegerField(
        help_text="Tahun angkatan mahasiswa, misal 2023 untuk mahasiswa angkatan 2023",
    )
    nama = models.CharField(
        max_length=20,
        help_text="Contoh: A, B, C",
    )
    peminatan = models.ForeignKey(
        Peminatan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="kelas",
        help_text="Kosongkan jika ini adalah kelas umum (bukan peminatan).",
    )

    def __str__(self):
        return f"{self.tahun_angkatan} {self.nama}"

    class Meta:
        verbose_name = "Kelas"
        verbose_name_plural = "Kelas"
        ordering = ["tahun_angkatan", "nama"]
        unique_together = ("tahun_angkatan", "nama", "peminatan")


class JadwalHarian(models.Model):
    HARI_CHOICES = [
        (0, "Senin"),
        (1, "Selasa"),
        (2, "Rabu"),
        (3, "Kamis"),
        (4, "Jumat"),
        (5, "Sabtu"),
        (6, "Minggu"),
    ]

    hari = models.PositiveSmallIntegerField(
        choices=HARI_CHOICES,
        unique=True,
    )
    jam_mulai = models.TimeField()
    jam_selesai = models.TimeField()
    istirahat_mulai = models.TimeField(help_text="Waktu mulai istirahat")
    istirahat_selesai = models.TimeField(help_text="Waktu selesai istirahat")

    def __str__(self):
        return self.get_hari_display()  # type: ignore

    class Meta:
        verbose_name = "Jadwal Harian"
        verbose_name_plural = "Pengaturan Jadwal Harian"
        ordering = ["hari"]


class Jadwal(models.Model):
    HARI_CHOICES = JadwalHarian.HARI_CHOICES  # Menggunakan ulang choices
    tahun_akademik = models.ForeignKey(
        TahunAkademik, on_delete=models.CASCADE, related_name="jadwal_set"
    )
    matakuliah = models.ForeignKey(MataKuliah, on_delete=models.CASCADE)
    dosen = models.ForeignKey(Dosen, on_delete=models.SET_NULL, null=True)
    kelas = models.ForeignKey(Kelas, on_delete=models.CASCADE)
    ruangan = models.ForeignKey(Ruangan, on_delete=models.SET_NULL, null=True)
    hari = models.PositiveSmallIntegerField(choices=HARI_CHOICES)
    jam_mulai = models.TimeField()
    jam_selesai = models.TimeField()

    def __str__(self):
        hari_display = self.get_hari_display()  # type: ignore
        return f"{self.matakuliah.nama} - {self.kelas} ({hari_display}, {self.jam_mulai:%H:%M}-{self.jam_selesai:%H:%M})"

    class Meta:
        verbose_name = "Jadwal Kuliah (Hasil)"
        verbose_name_plural = "Jadwal Kuliah (Hasil)"
        ordering = ["tahun_akademik", "hari", "jam_mulai", "kelas"]
        unique_together = [
            ("tahun_akademik", "hari", "jam_mulai", "ruangan"),
            ("tahun_akademik", "hari", "jam_mulai", "kelas"),
            ("tahun_akademik", "hari", "jam_mulai", "dosen"),
        ]
