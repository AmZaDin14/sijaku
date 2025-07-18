# Generated by Django 5.2.1 on 2025-06-30 00:48

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Peminatan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kode', models.CharField(max_length=10, unique=True)),
                ('nama', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name': 'Peminatan',
                'verbose_name_plural': 'Peminatan',
                'ordering': ['kode'],
            },
        ),
        migrations.CreateModel(
            name='Ruangan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nama', models.CharField(max_length=50, unique=True)),
                ('jenis', models.CharField(choices=[('kelas', 'Ruang Kelas'), ('lab', 'Lab Komputer')], max_length=10)),
                ('kapasitas', models.PositiveIntegerField(help_text='Jumlah kelas yang dapat ditampung')),
            ],
            options={
                'verbose_name': 'Ruangan',
                'verbose_name_plural': 'Ruangan',
                'ordering': ['nama'],
            },
        ),
        migrations.CreateModel(
            name='Dosen',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nidn', models.CharField(max_length=20, unique=True)),
                ('nama', models.CharField(max_length=100)),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='dosen', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Dosen',
                'verbose_name_plural': 'Dosen',
                'ordering': ['nama'],
            },
        ),
        migrations.CreateModel(
            name='MataKuliah',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kode', models.CharField(max_length=10, unique=True)),
                ('nama', models.CharField(max_length=100)),
                ('sks', models.PositiveIntegerField()),
                ('semester', models.PositiveSmallIntegerField(default=1)),
                ('tipe', models.CharField(choices=[('teori', 'Teori'), ('praktik', 'Praktik')], default='teori', max_length=10)),
                ('peminatan', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='matakuliah', to='data.peminatan')),
            ],
            options={
                'verbose_name': 'Mata Kuliah',
                'verbose_name_plural': 'Mata Kuliah',
                'ordering': ['semester', 'kode'],
            },
        ),
        migrations.CreateModel(
            name='TahunAkademik',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tahun', models.CharField(max_length=9)),
                ('semester', models.CharField(choices=[('ganjil', 'Ganjil'), ('genap', 'Genap')], default='ganjil', max_length=10)),
                ('aktif', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Tahun Akademik',
                'verbose_name_plural': 'Tahun Akademik',
                'ordering': ['-tahun'],
                'unique_together': {('tahun', 'semester')},
            },
        ),
        migrations.CreateModel(
            name='ValidasiPemetaanDosenMK',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('diajukan', 'Diajukan'), ('disetujui', 'Disetujui'), ('ditolak', 'Ditolak')], default='draft', max_length=20)),
                ('diajukan_pada', models.DateTimeField(blank=True, null=True)),
                ('divalidasi_pada', models.DateTimeField(blank=True, null=True)),
                ('catatan', models.TextField(blank=True)),
                ('diajukan_oleh', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pengajuan_pemetaan', to='data.dosen')),
                ('divalidasi_oleh', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='validasi_pemetaan_wd1', to='data.dosen')),
                ('tahun_akademik', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='validasi_pemetaan', to='data.tahunakademik')),
            ],
            options={
                'verbose_name': 'Validasi Pemetaan Dosen-MK',
                'verbose_name_plural': 'Validasi Pemetaan Dosen-MK',
            },
        ),
        migrations.CreateModel(
            name='ValidasiPemetaanDosenMKLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('aksi', models.CharField(choices=[('draft', 'Draft'), ('diajukan', 'Diajukan'), ('disetujui', 'Disetujui'), ('ditolak', 'Ditolak')], max_length=50)),
                ('waktu', models.DateTimeField(default=django.utils.timezone.now)),
                ('catatan', models.TextField(blank=True)),
                ('oleh', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='data.dosen')),
                ('validasi', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='histori', to='data.validasipemetaandosenmk')),
            ],
            options={
                'verbose_name': 'Histori Validasi Pemetaan Dosen-MK',
                'verbose_name_plural': 'Histori Validasi Pemetaan Dosen-MK',
                'ordering': ['-waktu'],
            },
        ),
        migrations.CreateModel(
            name='Jabatan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nama', models.CharField(choices=[('kaprodi', 'Kaprodi'), ('wd1', 'WD1')], max_length=20, unique=True)),
                ('dosen', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='jabatan', to='data.dosen')),
            ],
            options={
                'verbose_name': 'Jabatan',
                'verbose_name_plural': 'Jabatan',
                'ordering': ['nama'],
                'unique_together': {('nama',)},
            },
        ),
        migrations.CreateModel(
            name='Kelas',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tahun_angkatan', models.PositiveIntegerField(help_text='Tahun angkatan mahasiswa, misal 2023 untuk mahasiswa angkatan 2023')),
                ('nama', models.CharField(help_text='Contoh: A, B, C', max_length=20)),
                ('peminatan', models.ForeignKey(blank=True, help_text='Kosongkan jika ini adalah kelas umum (bukan peminatan).', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='kelas', to='data.peminatan')),
            ],
            options={
                'verbose_name': 'Kelas',
                'verbose_name_plural': 'Kelas',
                'ordering': ['tahun_angkatan', 'nama'],
                'unique_together': {('tahun_angkatan', 'nama', 'peminatan')},
            },
        ),
        migrations.CreateModel(
            name='PemetaanDosenMK',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dosen_pengampu', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pengampu_matakuliah', to='data.dosen')),
                ('matakuliah', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='penyelenggaraan', to='data.matakuliah')),
                ('tahun_akademik', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='penyelenggaraan', to='data.tahunakademik')),
            ],
            options={
                'verbose_name': 'Pemetaan Dosen-MK',
                'verbose_name_plural': 'Pemetaan Dosen-MK',
                'ordering': ['tahun_akademik', 'matakuliah'],
                'unique_together': {('tahun_akademik', 'matakuliah')},
            },
        ),
    ]
