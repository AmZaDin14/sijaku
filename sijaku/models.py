from django.db import models
from accounts.models import CustomUser

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
