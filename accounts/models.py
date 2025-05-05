# accounts/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Username (NIDN atau ID Staf) harus diisi")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(username, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=20, unique=True)  # NIDN atau ID Staf
    ROLE_CHOICES = (
        ('dosen', 'Dosen'),
        ('staf', 'Staf'),
        ('admin', 'Admin'),
    )
    JABATAN_CHOICES = (
        ('kaprodi', 'Kaprodi'),
        ('wd1', 'Wakil Dekan 1'),
        ('-', 'Tidak Ada'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    jabatan = models.CharField(max_length=20, choices=JABATAN_CHOICES, default='-')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['role']

    def __str__(self):
        return self.username
