from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from associations.models import Association, Membership

from .models import User


PUBLIC_USERNAME_HELP = "Detta namn visas offentligt, bland annat i topplistor."


def _association_field():
    return forms.ModelMultipleChoiceField(
        label="Föreningar",
        queryset=Association.objects.order_by("name"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )


def _sync_memberships(user, associations):
    selected_ids = {association.pk for association in associations}
    Membership.objects.filter(user=user).exclude(association_id__in=selected_ids).delete()
    existing_ids = set(
        Membership.objects.filter(user=user, association_id__in=selected_ids).values_list(
            "association_id", flat=True
        )
    )
    Membership.objects.bulk_create(
        [
            Membership(user=user, association_id=association_id)
            for association_id in selected_ids - existing_ids
        ]
    )


class RegistrationForm(UserCreationForm):
    name = forms.CharField(label="Namn", max_length=300)
    public_username = forms.CharField(
        label="Publikt användarnamn",
        max_length=50,
        help_text=PUBLIC_USERNAME_HELP,
    )
    email = forms.EmailField(label="E-post")
    associations = _association_field()

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "name",
            "public_username",
            "email",
            "associations",
            "password1",
            "password2",
        )

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
            _sync_memberships(user, self.cleaned_data["associations"])
        return user


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="E-post")

    def clean(self):
        email = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if email is not None and password:
            users = User.objects.filter(email__iexact=email)
            if users.count() != 1:
                raise self.get_invalid_login_error()

            user = users.first()
            self.user_cache = authenticate(
                self.request,
                username=user.get_username(),
                password=password,
            )
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        label="Förnamn",
        max_length=150,
        required=False,
    )
    last_name = forms.CharField(
        label="Efternamn",
        max_length=150,
        required=False,
    )
    display_name = forms.CharField(label="Visningsnamn", max_length=150)
    public_username = forms.CharField(
        label="Publikt användarnamn",
        max_length=50,
        help_text=PUBLIC_USERNAME_HELP,
    )
    associations = _association_field()

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "public_username",
            "display_name",
            "location",
            "avatar_url",
        )
        labels = {
            "location": "Ort",
            "avatar_url": "Profilbild (URL)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and not self.is_bound:
            self.fields["associations"].initial = self.instance.memberships.values_list(
                "association_id", flat=True
            )

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

    def clean_first_name(self):
        return self.cleaned_data["first_name"].strip()

    def clean_last_name(self):
        return self.cleaned_data["last_name"].strip()

    def clean_location(self):
        return self.cleaned_data["location"].strip()

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            _sync_memberships(user, self.cleaned_data["associations"])
        return user
