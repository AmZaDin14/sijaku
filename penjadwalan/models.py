from django.db import models

from sijaku.models import Dosen, Kelas, MataKuliah, Ruangan, TahunAkademik

# Create your models here.


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
