from django import forms

from .models import (
    Dosen,
    Jabatan,
    MataKuliah,
    PemetaanDosenMK,
    Peminatan,
    Ruangan,
    TahunAkademik,
)


class DosenForm(forms.ModelForm):
    class Meta:
        model = Dosen
        fields = ["nidn", "nama"]
        widgets = {
            "nidn": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "nama": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
        }


class JabatanForm(forms.ModelForm):
    class Meta:
        model = Jabatan
        fields = ["nama", "dosen"]
        widgets = {
            "nama": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "dosen": forms.Select(attrs={"class": "select select-bordered w-full"}),
        }


class MataKuliahForm(forms.ModelForm):
    class Meta:
        model = MataKuliah
        fields = ["kode", "nama", "sks", "semester", "tipe", "peminatan"]
        widgets = {
            "kode": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "nama": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "sks": forms.NumberInput(
                attrs={"class": "input input-bordered w-full", "min": 1}
            ),
            "semester": forms.NumberInput(
                attrs={"class": "input input-bordered w-full", "min": 1}
            ),
            "tipe": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "peminatan": forms.Select(attrs={"class": "select select-bordered w-full"}),
        }


class TahunAkademikForm(forms.ModelForm):
    tahun_mulai = forms.IntegerField(
        min_value=2000,
        max_value=2100,
        label="Tahun Mulai",
        widget=forms.NumberInput(
            attrs={
                "class": "input input-bordered w-full",
                "placeholder": "2024",
            }
        ),
    )
    tahun_berakhir = forms.IntegerField(
        label="Tahun Berakhir",
        required=False,
        widget=forms.NumberInput(
            attrs={
                "class": "input input-bordered w-full bg-base-200 cursor-not-allowed",
                "readonly": True,
                "tabindex": "-1",
            }
        ),
    )

    class Meta:
        model = TahunAkademik
        fields = ["tahun_mulai", "tahun_berakhir", "semester", "aktif"]
        widgets = {
            "semester": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "aktif": forms.CheckboxInput(attrs={"class": "checkbox checkbox-primary"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tahun = None
        if self.instance and self.instance.tahun:
            tahun = self.instance.tahun.split("/")[0]
        if self.data.get("tahun_mulai"):
            tahun = self.data["tahun_mulai"]
        if tahun:
            try:
                tahun = int(tahun)
                self.fields["tahun_berakhir"].initial = tahun + 1
            except Exception:
                self.fields["tahun_berakhir"].initial = ""
        else:
            self.fields["tahun_berakhir"].initial = ""
        if self.instance and self.instance.tahun:
            tahun_mulai = self.instance.tahun.split("/")[0]
            self.fields["tahun_mulai"].initial = tahun_mulai

    def clean(self):
        cleaned_data = super().clean()
        tahun_mulai = cleaned_data.get("tahun_mulai")
        semester = cleaned_data.get("semester")
        aktif = cleaned_data.get("aktif")
        if tahun_mulai:
            cleaned_data["tahun_berakhir"] = tahun_mulai + 1
            tahun_str = f"{tahun_mulai}/{tahun_mulai + 1}"
            cleaned_data["tahun"] = tahun_str
            # Cek duplikasi tahun+semester
            from .models import TahunAkademik

            if (
                TahunAkademik.objects.filter(tahun=tahun_str, semester=semester)
                .exclude(pk=self.instance.pk)
                .exists()
            ):
                raise forms.ValidationError(
                    "Tahun akademik dan semester yang sama sudah ada."
                )
        # Cek hanya 1 tahun akademik aktif
        if aktif:
            from .models import TahunAkademik
        return cleaned_data

    def save(self, commit=True):
        # Jika tahun ini di-set aktif, nonaktifkan tahun lain
        if self.cleaned_data.get("aktif"):
            from .models import TahunAkademik

            TahunAkademik.objects.filter(aktif=True).exclude(
                pk=self.instance.pk
            ).update(aktif=False)
        self.instance.tahun = (
            f"{self.cleaned_data['tahun_mulai']}/{self.cleaned_data['tahun_berakhir']}"
        )
        return super().save(commit=commit)


class RuanganForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["kapasitas"].label = "Kapasitas (Kelas)"

    class Meta:
        model = Ruangan
        fields = ["nama", "jenis", "kapasitas"]
        widgets = {
            "nama": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "jenis": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "kapasitas": forms.NumberInput(
                attrs={"class": "input input-bordered w-full", "min": 1}
            ),
        }


class PemetaanDosenMKForm(forms.ModelForm):
    def __init__(self, *args, matakuliah_qs=None, dosen_qs=None, **kwargs):
        super().__init__(*args, **kwargs)
        if matakuliah_qs is not None:
            self.fields["matakuliah"] = forms.ModelChoiceField(
                queryset=matakuliah_qs,
                widget=forms.Select(attrs={"class": "select select-bordered w-full"}),
            )
        if dosen_qs is not None:
            self.fields["dosen_pengampu"] = forms.ModelChoiceField(
                queryset=dosen_qs,
                required=False,
                widget=forms.Select(attrs={"class": "select select-bordered w-full"}),
            )

    class Meta:
        model = PemetaanDosenMK
        fields = ["matakuliah", "dosen_pengampu"]
        widgets = {
            "matakuliah": forms.Select(
                attrs={"class": "select select-bordered w-full"}
            ),
            "dosen_pengampu": forms.Select(
                attrs={"class": "select select-bordered w-full"}
            ),
        }


class PeminatanForm(forms.ModelForm):
    class Meta:
        model = Peminatan
        fields = ["kode", "nama"]
        widgets = {
            "kode": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "nama": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
        }
