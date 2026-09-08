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
        if User.objects.filter(username__iexact=email).exists():
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
