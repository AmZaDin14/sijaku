from django.db import models
from accounts.models import CustomUser
from django.core.exceptions import ValidationError

class Dosen(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    nidn = models.CharField(max_length=20, unique=True)
    nama = models.CharField(max_length=100)

    def __str__(self):
        return self.nama

class Staf(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    id_staf = models.CharField(max_length=20, unique=True)
    nama = models.CharField(max_length=100)

    def __str__(self):
        return self.nama

class Ruangan(models.Model):
    TIPE_RUANGAN_CHOICES = [
        ('kelas', 'Kelas'),
        ('lab', 'Lab Komputer'),
    ]

    kode = models.CharField(max_length=10, unique=True)
    nama = models.CharField(max_length=100)
    kapasitas = models.PositiveIntegerField()
    tipe = models.CharField(max_length=10, choices=TIPE_RUANGAN_CHOICES)

    def __str__(self):
        return f"{self.nama} ({self.kode})"

class MataKuliah(models.Model):
    TIPE_MK_CHOICES = [
        ('teori', 'Teori'),
        ('praktik', 'Praktik'),
    ]

    kode = models.CharField(max_length=10, unique=True)
    nama = models.CharField(max_length=100)
    sks = models.PositiveIntegerField()
    semester = models.PositiveIntegerField()
    tipe = models.CharField(max_length=10, choices=TIPE_MK_CHOICES)

    # Relasi Many-to-Many: usulan dosen
    usulan_dosen = models.ManyToManyField('Dosen', blank=True, related_name='mata_kuliah_diusulkan')

    # Dosen pengampu (hanya satu)
    dosen_pengampu = models.ForeignKey('Dosen', null=True, blank=True, on_delete=models.SET_NULL,
                                       related_name='mata_kuliah_diampu')

    def __str__(self):
        return f"{self.nama} ({self.kode})"

class Hari(models.Model):
    nama = models.CharField(max_length=10)  # Contoh: Senin, Selasa, dst.

    def __str__(self):
        return self.nama

class JamKuliah(models.Model):
    mulai = models.TimeField()
    selesai = models.TimeField()

    def __str__(self):
        return f"{self.mulai.strftime('%H:%M')} - {self.selesai.strftime('%H:%M')}"

class JadwalPerkuliahan(models.Model):
    matakuliah = models.ForeignKey(MataKuliah, on_delete=models.CASCADE)
    dosen = models.ForeignKey(Dosen, on_delete=models.CASCADE)
    ruangan = models.ForeignKey(Ruangan, on_delete=models.CASCADE)
    hari = models.ForeignKey(Hari, on_delete=models.CASCADE)
    jam = models.ForeignKey(JamKuliah, on_delete=models.CASCADE)
    kelas = models.CharField(max_length=5)  # Misal: A, B, C

    def __str__(self):
        return f"{self.matakuliah.nama} - {self.kelas} ({self.hari.nama} {self.jam})"

    def clean(self):
        # Validasi: teori harus pakai ruangan kelas, praktik harus pakai lab komputer
        if self.matakuliah.tipe == 'teori' and self.ruangan.tipe != 'kelas':
            raise ValidationError("Mata kuliah teori harus menggunakan ruangan kelas.")
        if self.matakuliah.tipe == 'praktik' and self.ruangan.tipe != 'lab':
            raise ValidationError("Mata kuliah praktik harus menggunakan lab komputer.")

    class Meta:
        unique_together = ('hari', 'jam', 'ruangan')  # Untuk mencegah bentrok ruangan