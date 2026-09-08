from django.conf import settings
from django.db import models

from associations.models import Association
from taxonomy.models import Species


class BreedingRegistration(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Utkast"
        SUBMITTED = "submitted", "Inskickad"
        APPROVED = "approved", "Godkänd"
        REJECTED = "rejected", "Avslagen"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="breeding_registrations",
        verbose_name="användare",
    )
    association = models.ForeignKey(
        Association,
        on_delete=models.PROTECT,
        related_name="breeding_registrations",
        verbose_name="förening",
    )
    species = models.ForeignKey(
        Species,
        on_delete=models.PROTECT,
        related_name="breeding_registrations",
        verbose_name="art",
    )
    breeding_date = models.DateField(verbose_name="odlingsdatum")
    description = models.TextField(verbose_name="beskrivning")
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="status",
    )
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name="inskickad")
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name="godkänd")
    awarded_breeding_class = models.CharField(
        max_length=6,
        choices=Species.BreedingClass.choices,
        blank=True,
        verbose_name="tilldelad odlingsklass",
    )
    awarded_points = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="tilldelade poäng",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reviewed_breeding_registrations",
        verbose_name="granskare",
    )
    review_comment = models.TextField(blank=True, verbose_name="granskningskommentar")

    class Meta:
        ordering = ["-breeding_date", "-pk"]
        verbose_name = "odlingsregistrering"
        verbose_name_plural = "odlingsregistreringar"

    def __str__(self):
        return f"{self.owner} – {self.species} – {self.breeding_date}"
