from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


PUBLIC_USERNAME_HELP = "Detta namn visas offentligt, bland annat i topplistor."


class RegistrationForm(UserCreationForm):
    name = forms.CharField(label="Namn", max_length=300)
    public_username = forms.CharField(
        label="Publikt användarnamn",
        max_length=50,
        help_text=PUBLIC_USERNAME_HELP,
    )
    email = forms.EmailField(label="E-post")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("name", "public_username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if (
            User.objects.filter(username__iexact=email).exists()
            or User.objects.filter(email__iexact=email).exists()
        ):
            raise forms.ValidationError("Det finns redan ett konto med den e-postadressen.")
        return email

    def clean_public_username(self):
        public_username = self.cleaned_data["public_username"].strip()
        if User.objects.filter(public_username__iexact=public_username).exists():
            raise forms.ValidationError("Det publika användarnamnet används redan.")
        return public_username

    def save(self, commit=True):
        user = super().save(commit=False)
        name = self.cleaned_data["name"].strip()
        email = self.cleaned_data["email"]
        first_name, separator, last_name = name.partition(" ")

        user.username = email
        user.email = email
        user.public_username = self.cleaned_data["public_username"]
        user.first_name = first_name
        user.last_name = last_name if separator else ""

        if commit:
            user.save()
        return user


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="E-post")


class ProfileForm(forms.ModelForm):
    display_name = forms.CharField(label="Visningsnamn", max_length=150)
    public_username = forms.CharField(
        label="Publikt användarnamn",
        max_length=50,
        help_text=PUBLIC_USERNAME_HELP,
    )

    class Meta:
        model = User
        fields = ("public_username", "display_name", "location", "avatar_url")
        labels = {
            "location": "Ort",
            "avatar_url": "Profilbild (URL)",
        }

    def clean_public_username(self):
        public_username = self.cleaned_data["public_username"].strip()
        if (
            User.objects.filter(public_username__iexact=public_username)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError("Det publika användarnamnet används redan.")
        return public_username

    def clean_display_name(self):
        display_name = self.cleaned_data["display_name"].strip()
        if not display_name:
            raise forms.ValidationError("Ange ett visningsnamn.")
        return display_name

    def clean_location(self):
        return self.cleaned_data["location"].strip()
