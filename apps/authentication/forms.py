from django import forms
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
    role = forms.ChoiceField(
        choices=PUBLIC_ROLES,
        widget=forms.Select(),
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

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Password tidak cocok.")
        return password2
