from django import forms
from .models import Dosen, Jabatan

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