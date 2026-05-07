import re

from django import forms
from django.core.exceptions import ValidationError

from .models import Voter


class VoterForm(forms.ModelForm):
    class Meta:
        model = Voter
        fields = ["nik", "npm", "email", "full_name", "faculty", "study_program", "status"]
        widgets = {
            "nik": forms.TextInput(attrs={"placeholder": "16 digit NIK"}),
            "npm": forms.TextInput(attrs={"placeholder": "NPM"}),
            "email": forms.EmailInput(attrs={"placeholder": "email@example.com"}),
            "full_name": forms.TextInput(attrs={"placeholder": "Nama lengkap"}),
            "faculty": forms.TextInput(attrs={"placeholder": "Fakultas"}),
            "study_program": forms.TextInput(attrs={"placeholder": "Program studi"}),
            "status": forms.Select(),
        }

    def clean_nik(self):
        nik = self.cleaned_data["nik"].strip()
        if not re.match(r"^\d{16}$", nik):
            raise ValidationError("NIK harus terdiri dari 16 digit angka.")
        return nik

    def clean_npm(self):
        npm = self.cleaned_data["npm"].strip()
        if not re.match(r"^\d+$", npm):
            raise ValidationError("NPM harus terdiri dari digit angka.")
        return npm

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        qs = Voter.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Email sudah digunakan oleh pemilih lain.")
        return email

    def clean_full_name(self):
        return self.cleaned_data["full_name"].strip()

    def clean_faculty(self):
        return self.cleaned_data["faculty"].strip()

    def clean_study_program(self):
        return self.cleaned_data["study_program"].strip()
