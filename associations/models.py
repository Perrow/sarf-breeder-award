from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import URLValidator
from urllib.parse import urlsplit


def _validate_social_url(value, hosts, platform):
    if not value:
        return
    URLValidator(schemes=["https"])(value)
    url = urlsplit(value)
    if (url.hostname or "").lower() not in hosts or url.username or url.password or url.port:
        raise ValidationError(f"Ange en giltig HTTPS-länk till {platform}.")


def validate_facebook_url(value):
    _validate_social_url(value, {"facebook.com", "www.facebook.com", "m.facebook.com", "web.facebook.com"}, "Facebook")


def validate_instagram_url(value):
    _validate_social_url(value, {"instagram.com", "www.instagram.com"}, "Instagram")


class Association(models.Model):
    name = models.CharField(max_length=200, verbose_name="namn")
    organization_number = models.CharField(max_length=50, blank=True, verbose_name="organisationsnummer")
    email = models.EmailField(blank=True, verbose_name="e-post")
    phone = models.CharField(max_length=50, blank=True, verbose_name="telefon")
    description = models.CharField(max_length=500, blank=True, verbose_name="beskrivning")
    website_url = models.URLField(max_length=500, blank=True, verbose_name="hemsida")
    facebook_url = models.URLField(max_length=500, blank=True, validators=[validate_facebook_url], verbose_name="Facebook")
    instagram_url = models.URLField(max_length=500, blank=True, validators=[validate_instagram_url], verbose_name="Instagram")
    address = models.CharField(max_length=255, blank=True, verbose_name="adress")
    postal_code = models.CharField(max_length=20, blank=True, verbose_name="postnummer")
    city = models.CharField(max_length=100, blank=True, verbose_name="ort")
    contact_person = models.CharField(max_length=200, blank=True, verbose_name="kontaktperson")
    note = models.TextField(blank=True, verbose_name="anteckning")

    class Meta:
        verbose_name = "förening"
        verbose_name_plural = "föreningar"

    def clean(self):
        super().clean()
        if self.name is not None and not self.name.strip():
            raise ValidationError({"name": "Ange föreningens namn."})

    def __str__(self):
        return self.name


class Membership(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name="användare",
    )
    association = models.ForeignKey(
        Association,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name="förening",
    )
    member_number = models.CharField(max_length=100, blank=True, verbose_name="medlemsnummer")
    phone = models.CharField(max_length=50, blank=True, verbose_name="telefon")
    association_data = models.TextField(blank=True, verbose_name="föreningsuppgifter")
    is_association_admin = models.BooleanField(default=False, verbose_name="föreningsadministratör")

    class Meta:
        verbose_name = "medlemskap"
        verbose_name_plural = "medlemskap"
        constraints = [
            models.UniqueConstraint(
                fields=("user", "association"),
                name="unique_user_association_membership",
            ),
        ]

    def __str__(self):
        return f"{self.user} – {self.association}"


class AssociationAdministratorManagement(Membership):
    class Meta:
        proxy = True
        verbose_name = "föreningsadministratör"
        verbose_name_plural = "Föreningsadministratörer"
