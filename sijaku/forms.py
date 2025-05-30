from django import forms
from .models import Dosen, Jabatan, MataKuliah, TahunAkademik, Ruangan

class DosenForm(forms.ModelForm):
    class Meta:
        model = Dosen
        fields = ['nidn', 'nama']
        widgets = {
            'nidn': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'nama': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
        }

class JabatanForm(forms.ModelForm):
    class Meta:
        model = Jabatan
        fields = ['nama', 'dosen']
        widgets = {
            'nama': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'dosen': forms.Select(attrs={'class': 'select select-bordered w-full'}),
        }

class MataKuliahForm(forms.ModelForm):
    class Meta:
        model = MataKuliah
        fields = ['kode', 'nama', 'sks', 'semester']
        widgets = {
            'kode': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'nama': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'sks': forms.NumberInput(attrs={'class': 'input input-bordered w-full', 'min': 1}),
            'semester': forms.NumberInput(attrs={'class': 'input input-bordered w-full', 'min': 1}),
        }

class TahunAkademikForm(forms.ModelForm):
    class Meta:
        model = TahunAkademik
        fields = ['tahun', 'semester', 'aktif']
        widgets = {
            'tahun': forms.TextInput(attrs={'class': 'input input-bordered w-full', 'placeholder': '2024/2025'}),
            'semester': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'aktif': forms.CheckboxInput(attrs={'class': 'checkbox checkbox-primary'}),
        }

class RuanganForm(forms.ModelForm):
    class Meta:
        model = Ruangan
        fields = ['nama', 'jenis', 'keterangan']
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'jenis': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'keterangan': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full', 'rows': 2}),
        }