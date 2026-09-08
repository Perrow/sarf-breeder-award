from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from associations.models import Association
from taxonomy.models import Species


class BreedingRegistration(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Utkast"
        SUBMITTED = "submitted", "Inskickad"
        APPROVED = "approved", "Godkänd"
        REJECTED = "rejected", "Avslagen"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="breeding_registrations", verbose_name="användare")
    association = models.ForeignKey(Association, on_delete=models.PROTECT, related_name="breeding_registrations", verbose_name="förening")
    species = models.ForeignKey(Species, on_delete=models.PROTECT, null=True, blank=True, related_name="breeding_registrations", verbose_name="art")
    proposed_genus_name = models.CharField(max_length=100, blank=True, verbose_name="föreslaget släkte")
    proposed_species_name = models.CharField(max_length=100, blank=True, verbose_name="föreslaget artnamn")
    proposed_common_name = models.CharField(max_length=200, blank=True, verbose_name="föreslaget populärnamn")
    taxonomy_needs_resolution = models.BooleanField(default=False, editable=False, verbose_name="taxonomi behöver lösas")
    breeding_date = models.DateField(verbose_name="odlingsdatum")
    description = models.TextField(verbose_name="beskrivning")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT, verbose_name="status")
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name="inskickad")
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name="godkänd")
    awarded_breeding_class = models.CharField(max_length=6, choices=Species.BreedingClass.choices, blank=True, verbose_name="tilldelad odlingsklass")
    awarded_points = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="tilldelade poäng")
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="reviewed_breeding_registrations", verbose_name="granskare")
    review_comment = models.TextField(blank=True, verbose_name="granskningskommentar")

    class Meta:
        ordering = ["-breeding_date", "-pk"]
        verbose_name = "odlingsregistrering"
        verbose_name_plural = "odlingsregistreringar"

    def clean(self):
        super().clean()
        if not self.species and not (self.proposed_genus_name.strip() and self.proposed_species_name.strip()):
            raise ValidationError("Välj en art eller ange både släkte och art i fritext.")

    def save(self, *args, **kwargs):
        self.taxonomy_needs_resolution = self.species_id is None
        super().save(*args, **kwargs)

    def __str__(self):
        species_name = self.species or f"{self.proposed_genus_name} {self.proposed_species_name}".strip()
        return f"{self.owner} – {species_name} – {self.breeding_date}"
