from django import forms
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator

from .models import User


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        validators=[UnicodeUsernameValidator()],
        widget=forms.TextInput(attrs={"placeholder": "Username"}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Password"}),
    )

    def clean_username(self):
        return self.cleaned_data["username"].strip()


class RegistrationForm(forms.ModelForm):
    PUBLIC_ROLES = [
        (User.Role.PEMILIH, "Pemilih"),
        (User.Role.PASLON, "Paslon"),
    ]

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(),
    )
    password2 = forms.CharField(
        label="Konfirmasi Password",
        widget=forms.PasswordInput(),
    )
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(
        choices=PUBLIC_ROLES,
        widget=forms.Select(),
    )

    # Extra fields for pemilih
    nik = forms.CharField(
        max_length=16,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "16 digit NIK"}),
    )
    npm = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "NPM"}),
    )
    faculty = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Fakultas"}),
    )
    study_program = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Program studi"}),
    )

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "role"]

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Username sudah digunakan.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email sudah digunakan.")
        return email

    def clean_first_name(self):
        return self.cleaned_data["first_name"].strip()

    def clean_last_name(self):
        return self.cleaned_data["last_name"].strip()

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Password tidak cocok.")
        if password2:
            user = User(
                username=self.cleaned_data.get("username", ""),
                email=self.cleaned_data.get("email", ""),
                first_name=self.cleaned_data.get("first_name", ""),
                last_name=self.cleaned_data.get("last_name", ""),
                role=self.cleaned_data.get("role", User.Role.PEMILIH),
            )
            validate_password(password2, user=user)
        return password2

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get("role")
        if role == User.Role.PEMILIH:
            nik = cleaned.get("nik", "").strip()
            npm = cleaned.get("npm", "").strip()
            faculty = cleaned.get("faculty", "").strip()
            study_program = cleaned.get("study_program", "").strip()

            import re
            if not nik or not re.match(r"^\d{16}$", nik):
                self.add_error("nik", "NIK harus terdiri dari 16 digit angka.")
            if not npm or not re.match(r"^\d+$", npm):
                self.add_error("npm", "NPM harus terdiri dari digit angka.")
            if not faculty:
                self.add_error("faculty", "Fakultas wajib diisi.")
            if not study_program:
                self.add_error("study_program", "Program studi wajib diisi.")

            from apps.voters.models import Voter
            if nik and not self.has_error("nik") and Voter.objects.filter(nik=nik).exists():
                self.add_error("nik", "NIK sudah terdaftar.")
            if npm and not self.has_error("npm") and Voter.objects.filter(npm=npm).exists():
                self.add_error("npm", "NPM sudah terdaftar.")
        return cleaned
