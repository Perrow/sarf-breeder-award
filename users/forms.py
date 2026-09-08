from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class RegistrationForm(UserCreationForm):
    name = forms.CharField(label="Namn", max_length=300)
    email = forms.EmailField(label="E-post")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("name", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if (
            User.objects.filter(username__iexact=email).exists()
            or User.objects.filter(email__iexact=email).exists()
        ):
            raise forms.ValidationError("Det finns redan ett konto med den e-postadressen.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        name = self.cleaned_data["name"].strip()
        email = self.cleaned_data["email"]
        first_name, separator, last_name = name.partition(" ")

        user.username = email
        user.email = email
        user.first_name = first_name
        user.last_name = last_name if separator else ""

        if commit:
            user.save()
        return user


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="E-post")


class ProfileForm(forms.ModelForm):
    display_name = forms.CharField(label="Visningsnamn", max_length=150)

    class Meta:
        model = User
        fields = ("display_name", "location", "avatar_url")
        labels = {
            "location": "Ort",
            "avatar_url": "Profilbild (URL)",
        }

    def clean_display_name(self):
        display_name = self.cleaned_data["display_name"].strip()
        if not display_name:
            raise forms.ValidationError("Ange ett visningsnamn.")
        return display_name

    def clean_location(self):
        return self.cleaned_data["location"].strip()
