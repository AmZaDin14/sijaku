# Generated by Django 5.2.1 on 2025-06-10 14:02

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data", "0014_jadwal"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="kelas",
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name="kelas",
            name="nama",
            field=models.CharField(help_text="Contoh: A, B, C", max_length=20),
        ),
        migrations.AlterUniqueTogether(
            name="kelas",
            unique_together={("tahun_angkatan", "nama", "peminatan")},
        ),
    ]
