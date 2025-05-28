from django.db import models


class Dosen(models.Model):
    nidn = models.CharField(max_length=20, unique=True)
    nama = models.CharField(max_length=100)

    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dosen'
    )

    def __str__(self):
        return self.nama

    class Meta:
        verbose_name = "Dosen"
        verbose_name_plural = "Dosen"
        ordering = ['nama']


class Jabatan(models.Model):
    JABATAN_CHOICES = [
        ("kaprodi", "Kaprodi"),
        ("wd1", "WD1"),
    ]
    nama = models.CharField(max_length=20, choices=JABATAN_CHOICES, unique=True)
    dosen = models.ForeignKey('Dosen', on_delete=models.CASCADE, related_name='jabatan', null=True, blank=True)

    def __str__(self):
        return dict(self.JABATAN_CHOICES).get(self.nama, self.nama)

    class Meta:
        verbose_name = "Jabatan"
        verbose_name_plural = "Jabatan"
        ordering = ['nama']
        unique_together = ('nama',)