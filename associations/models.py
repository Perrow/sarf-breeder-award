from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Association(models.Model):
    name = models.CharField(max_length=200)
    organization_number = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    website_url = models.URLField(max_length=500, blank=True, verbose_name="hemsida")
    address = models.CharField(max_length=255, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

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
    )
    association = models.ForeignKey(
        Association,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    member_number = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    association_data = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "association"),
                name="unique_user_association_membership",
            ),
        ]

    def __str__(self):
        return f"{self.user} – {self.association}"
