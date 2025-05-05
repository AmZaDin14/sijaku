# accounts/forms.py
from django import forms
from .models import CustomUser
from sijaku.models import Dosen, Staf

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full px-3 py-2 border rounded-xl'
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full px-3 py-2 border rounded-xl'
    }))

    class Meta:
        model = CustomUser
        fields = ['username', 'password', 'confirm_password', 'role']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-xl'}),
            'role': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-xl'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter: role admin tidak muncul di form
        self.fields['role'].choices = [
            (k, v) for k, v in CustomUser.ROLE_CHOICES if k != 'admin'
        ]

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        role = cleaned_data.get("role")
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Password dan konfirmasi tidak cocok")

        # Validasi username berdasarkan role
        if role == 'dosen':
            if not Dosen.objects.filter(nidn=username).exists():
                raise forms.ValidationError("NIDN tidak ditemukan di data dosen")
        elif role == 'staf':
            if not Staf.objects.filter(id_staf=username).exists():
                raise forms.ValidationError("ID Staf tidak ditemukan di data staf")

        return cleaned_data

    def save(self, commit=True):
        # Simpan atau perbarui CustomUser terlebih dahulu
        user = super().save(commit=False)

        # Set password terenkripsi
        user.set_password(self.cleaned_data["password"])  # Enkripsi password sebelum disimpan

        if commit:
            user.save()

        # Tentukan role dan kaitkan dengan Dosen atau Staf
        role = self.cleaned_data.get('role')

        # Periksa apakah user sudah memiliki entri Dosen atau Staf
        if role == 'dosen':
            # Update jika sudah ada, jika belum, buat baru
            dosen = Dosen.objects.get(nidn=user.username)
            dosen.user = user
            dosen.save()
        elif role == 'staf':
            # Update jika sudah ada, jika belum, buat baru
            staf = Staf.objects.get(id_staf=user.username)
            staf.user = user
            staf.save()

        return user

