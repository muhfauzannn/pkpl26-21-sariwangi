from django import forms
from django.forms import inlineformset_factory

from .models import Candidate, CandidateMember


class CandidateRegistrationForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ["name", "visi", "misi", "photo"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Nama paslon"}),
            "visi": forms.Textarea(attrs={"rows": 4, "placeholder": "Visi paslon"}),
            "misi": forms.Textarea(attrs={"rows": 4, "placeholder": "Misi paslon"}),
        }

    def clean_name(self):
        return self.cleaned_data["name"].strip()

    def clean_visi(self):
        visi = self.cleaned_data["visi"].strip()
        if len(visi) < 10:
            raise forms.ValidationError("Visi terlalu pendek (minimal 10 karakter).")
        return visi

    def clean_misi(self):
        misi = self.cleaned_data["misi"].strip()
        if len(misi) < 10:
            raise forms.ValidationError("Misi terlalu pendek (minimal 10 karakter).")
        return misi


class CandidateMemberForm(forms.ModelForm):
    class Meta:
        model = CandidateMember
        fields = ["name", "role", "photo"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Nama anggota"}),
            "role": forms.TextInput(attrs={"placeholder": "Jabatan/Peran"}),
        }

    def clean_name(self):
        return self.cleaned_data["name"].strip()

    def clean_role(self):
        return self.cleaned_data["role"].strip()


CandidateMemberFormSet = inlineformset_factory(
    Candidate,
    CandidateMember,
    form=CandidateMemberForm,
    extra=2,
    max_num=5,
    can_delete=True,
)
