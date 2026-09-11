from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from associations.models import Association
from taxonomy.models import Genus, Species, SpeciesGroup


def current_competition_year():
    return timezone.localdate().year


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


class SpeciesReclassificationRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Väntar på beslut"
        APPROVED = "approved", "Godkänd"
        REJECTED = "rejected", "Avslagen"

    species = models.ForeignKey(
        Species,
        on_delete=models.PROTECT,
        related_name="reclassification_requests",
        verbose_name="art",
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="species_reclassification_requests",
        verbose_name="begärd av",
    )
    current_breeding_class = models.CharField(
        max_length=6,
        choices=Species.BreedingClass.choices,
        verbose_name="klass vid begäran",
    )
    requested_breeding_class = models.CharField(
        max_length=6,
        choices=Species.BreedingClass.choices,
        verbose_name="önskad klass",
    )
    reason = models.TextField(verbose_name="motivering")
    status = models.CharField(
        max_length=8,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="status",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="skapad")
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="decided_species_reclassification_requests",
        verbose_name="beslutad av",
    )
    decided_at = models.DateTimeField(null=True, blank=True, verbose_name="beslutad")
    decision_comment = models.TextField(blank=True, verbose_name="beslutskommentar")

    class Meta:
        ordering = ("-created_at", "-pk")
        verbose_name = "omklassningsbegäran"
        verbose_name_plural = "omklassningsbegäranden"
        constraints = [
            models.UniqueConstraint(
                fields=("species",),
                condition=Q(status="pending"),
                name="unique_pending_reclassification_per_species",
            ),
        ]

    def clean(self):
        super().clean()
        if self.requested_breeding_class == self.current_breeding_class:
            raise ValidationError(
                {"requested_breeding_class": "Den önskade klassen måste skilja sig från den nuvarande."}
            )
        if self.reason is not None and not self.reason.strip():
            raise ValidationError({"reason": "Motivering måste anges."})

    def __str__(self):
        return f"{self.species}: {self.get_current_breeding_class_display()} → {self.get_requested_breeding_class_display()}"


class AssociationCompetitionSettings(models.Model):
    effective_from_year = models.PositiveIntegerField(
        default=current_competition_year,
        unique=True,
        verbose_name="gäller från och med år",
    )
    default_max_registrations_per_genus = models.PositiveIntegerField(
        verbose_name="standard: max odlingar per medlem och genus"
    )

    class Meta:
        ordering = ("-effective_from_year",)
        verbose_name = "inställning för föreningstävling"
        verbose_name_plural = "inställningar för föreningstävling"

    def clean(self):
        super().clean()
        if (
            self.default_max_registrations_per_genus is not None
            and self.default_max_registrations_per_genus < 1
        ):
            raise ValidationError(
                {"default_max_registrations_per_genus": "Maxantalet måste vara minst 1."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"Från {self.effective_from_year}: max "
            f"{self.default_max_registrations_per_genus} per medlem och genus"
        )


class AssociationCompetitionLimit(models.Model):
    effective_from_year = models.PositiveIntegerField(
        default=current_competition_year,
        verbose_name="gäller från och med år",
    )
    genus = models.ForeignKey(
        Genus,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="association_competition_limits",
        verbose_name="släkte",
    )
    species_group = models.ForeignKey(
        SpeciesGroup,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="association_competition_limits",
        verbose_name="artgrupp",
    )
    max_registrations_per_member = models.PositiveIntegerField(
        verbose_name="max odlingar per medlem och år"
    )

    class Meta:
        verbose_name = "begränsning för föreningstävling"
        verbose_name_plural = "begränsningar för föreningstävling"
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(genus__isnull=False, species_group__isnull=True)
                    | Q(genus__isnull=True, species_group__isnull=False)
                ),
                name="association_limit_exactly_one_taxonomy_target",
            ),
            models.UniqueConstraint(
                fields=("effective_from_year", "genus"),
                condition=Q(genus__isnull=False),
                name="unique_association_genus_limit_per_year",
            ),
            models.UniqueConstraint(
                fields=("effective_from_year", "species_group"),
                condition=Q(species_group__isnull=False),
                name="unique_association_group_limit_per_year",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if (self.genus_id is None) == (self.species_group_id is None):
            errors["genus"] = "Ange exakt ett släkte eller en artgrupp."
            errors["species_group"] = "Ange exakt ett släkte eller en artgrupp."
        if self.max_registrations_per_member is not None and self.max_registrations_per_member < 1:
            errors["max_registrations_per_member"] = "Maxantalet måste vara minst 1."

        if self.species_group_id:
            if self.species_group.species.exists():
                errors["species_group"] = (
                    "Artgrupper med direktkopplade arter kan inte användas som begränsning."
                )
            elif not self.species_group.genera.exists():
                errors["species_group"] = (
                    "Artgruppen måste innehålla minst ett släkte för att kunna användas."
                )
            else:
                overlapping_genus = (
                    AssociationCompetitionLimit.objects.filter(
                        genus__in=self.species_group.genera.all(),
                        effective_from_year__lte=self.effective_from_year,
                    )
                    .exclude(pk=self.pk)
                    .select_related("genus")
                    .order_by("-effective_from_year")
                    .first()
                )
                if overlapping_genus:
                    errors["species_group"] = (
                        f"Artgruppen överlappar en regel för släktet {overlapping_genus.genus}."
                    )

        if self.genus_id:
            overlapping_group = (
                AssociationCompetitionLimit.objects.filter(
                    species_group__genera=self.genus,
                    effective_from_year__lte=self.effective_from_year,
                )
                .exclude(pk=self.pk)
                .select_related("species_group")
                .order_by("-effective_from_year")
                .first()
            )
            if overlapping_group:
                errors["genus"] = (
                    f"Släktet ingår redan i artgruppen {overlapping_group.species_group}, "
                    "som har en begränsningsregel."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        target = self.genus or self.species_group
        return (
            f"{target}: max {self.max_registrations_per_member} per medlem och år "
            f"(från {self.effective_from_year})"
        )
