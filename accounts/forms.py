from django import forms

from data.models import Dosen

from .models import User


class UserRegistrationForm(forms.ModelForm):
    username = forms.CharField(label="NIDN")
    password = forms.CharField(widget=forms.PasswordInput, label="Kata Sandi")
    password_confirm = forms.CharField(
        widget=forms.PasswordInput, label="Konfirmasi Kata Sandi"
    )

    class Meta:
        model = User
        fields = ["username", "password", "password_confirm"]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        username = cleaned_data.get("username")

        if password and len(password) < 6:
            self.add_error("password", "Kata sandi minimal 6 karakter.")

        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "Kata sandi tidak cocok.")

        if username and not Dosen.objects.filter(nidn=username).exists():
            self.add_error("username", "NIDN tidak cocok dengan data dosen yang ada.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            # Assign user ke Dosen dengan nidn yang sama
            from data.models import Dosen

            try:
                dosen = Dosen.objects.get(nidn=user.username)
                dosen.user = user
                dosen.save()
            except Dosen.DoesNotExist:
                pass
        return user
