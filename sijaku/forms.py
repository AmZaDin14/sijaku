from django import forms

from .models import Dosen, Jabatan, MataKuliah, Ruangan, TahunAkademik


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
        fields = ["kode", "nama", "sks", "semester"]
        widgets = {
            "kode": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "nama": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "sks": forms.NumberInput(
                attrs={"class": "input input-bordered w-full", "min": 1}
            ),
            "semester": forms.NumberInput(
                attrs={"class": "input input-bordered w-full", "min": 1}
            ),
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
    class Meta:
        model = Ruangan
        fields = ["nama", "jenis", "keterangan"]
        widgets = {
            "nama": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "jenis": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "keterangan": forms.Textarea(
                attrs={"class": "textarea textarea-bordered w-full", "rows": 2}
            ),
        }
