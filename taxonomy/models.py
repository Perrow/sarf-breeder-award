from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Genus(models.Model):
    scientific_name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["scientific_name"]
        verbose_name = "genus"
        verbose_name_plural = "genera"

    def __str__(self):
        return self.scientific_name


class SpeciesGroup(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="namn")
    genera = models.ManyToManyField(
        Genus,
        blank=True,
        related_name="species_groups",
        verbose_name="släkten",
    )
    species = models.ManyToManyField(
        "Species",
        blank=True,
        related_name="direct_species_groups",
        verbose_name="arter",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "artgrupp"
        verbose_name_plural = "artgrupper"

    def __str__(self):
        return self.name


class Species(models.Model):
    class BreedingClass(models.TextChoices):
        BRONZE = "bronze", "Brons"
        SILVER = "silver", "Silver"
        GOLD = "gold", "Guld"

    genus = models.ForeignKey(
        Genus,
        on_delete=models.PROTECT,
        related_name="species",
        verbose_name="släkte",
    )
    scientific_name = models.CharField(max_length=100, verbose_name="artnamn")
    common_name = models.CharField(max_length=200, verbose_name="populärnamn")
    english_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="engelskt namn",
    )
    breeding_class = models.CharField(
        max_length=6,
        choices=BreedingClass.choices,
        verbose_name="odlingsklass",
    )
    is_active = models.BooleanField(default=True, verbose_name="aktiv")

    class Meta:
        ordering = ["genus__scientific_name", "scientific_name"]
        verbose_name = "art"
        verbose_name_plural = "arter"
        constraints = [
            models.UniqueConstraint(
                fields=("genus", "scientific_name"),
                name="unique_genus_species_scientific_name",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.scientific_name is not None and not self.scientific_name.strip():
            errors["scientific_name"] = "Ange ett artnamn."
        if self.common_name is not None and not self.common_name.strip():
            errors["common_name"] = "Ange ett populärnamn."
        if errors:
            raise ValidationError(errors)

    def get_species_groups(self):
        return SpeciesGroup.objects.filter(
            Q(genera=self.genus) | Q(species=self)
        ).distinct()

    def __str__(self):
        return f"{self.genus} {self.scientific_name}"


class SpeciesSynonym(models.Model):
    species = models.ForeignKey(
        Species,
        on_delete=models.CASCADE,
        related_name="synonyms",
        verbose_name="art",
    )
    scientific_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="vetenskapligt namn",
    )
    common_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="populärnamn",
    )

    class Meta:
        ordering = ["scientific_name", "common_name"]
        verbose_name = "artsynonym"
        verbose_name_plural = "artsynonymer"
        constraints = [
            models.CheckConstraint(
                condition=(
                    (Q(scientific_name="") & ~Q(common_name=""))
                    | (~Q(scientific_name="") & Q(common_name=""))
                ),
                name="species_synonym_exactly_one_name",
            ),
            models.UniqueConstraint(
                fields=("species", "scientific_name"),
                condition=~Q(scientific_name=""),
                name="unique_species_synonym_scientific_name",
            ),
            models.UniqueConstraint(
                fields=("species", "common_name"),
                condition=~Q(common_name=""),
                name="unique_species_synonym_common_name",
            ),
        ]

    def __str__(self):
        return self.scientific_name or self.common_name
