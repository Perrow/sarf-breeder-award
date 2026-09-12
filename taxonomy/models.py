from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Value
from django.db.models.functions import Concat, Lower


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
    is_visible = models.BooleanField(default=True, verbose_name="synlig för användare")
    genera = models.ManyToManyField(Genus, blank=True, related_name="species_groups", verbose_name="släkten")
    species = models.ManyToManyField("Species", blank=True, related_name="direct_species_groups", verbose_name="arter")

    class Meta:
        ordering = ["name"]
        verbose_name = "artgrupp"
        verbose_name_plural = "artgrupper"

    def __str__(self):
        return self.name


class Geography(models.Model):
    name = models.CharField(max_length=100, verbose_name="namn")

    class Meta:
        ordering = ["name"]
        verbose_name = "geografi"
        verbose_name_plural = "geografier"
        constraints = [models.UniqueConstraint(Lower("name"), name="unique_geography_name_ci")]

    def __str__(self):
        return self.name


class SpeciesQuerySet(models.QuerySet):
    def available_for_registration(self):
        return self.filter(is_active=True)

    def search(self, query, include_inactive=False):
        terms = (query or "").split()
        if not terms:
            return self.none()
        queryset = self if include_inactive else self.available_for_registration()
        queryset = queryset.annotate(
            full_scientific_name=Concat("genus__scientific_name", Value(" "), "scientific_name")
        )
        for term in terms:
            queryset = queryset.filter(
                Q(full_scientific_name__icontains=term)
                | Q(common_name__icontains=term)
                | Q(english_name__icontains=term)
                | Q(cl_number__icontains=term)
                | Q(scientific_synonyms__scientific_name__icontains=term)
                | Q(common_name_synonyms__common_name__icontains=term)
                | Q(geographies__name__icontains=term)
            )
        return queryset.distinct()


class Species(models.Model):
    class BreedingClass(models.TextChoices):
        BRONZE = "bronze", "Brons"
        SILVER = "silver", "Silver"
        GOLD = "gold", "Guld"

    genus = models.ForeignKey(Genus, on_delete=models.PROTECT, related_name="species", verbose_name="släkte")
    scientific_name = models.CharField(max_length=100, verbose_name="artnamn")
    common_name = models.CharField(max_length=200, verbose_name="populärnamn")
    english_name = models.CharField(max_length=200, blank=True, verbose_name="engelskt namn")
    cl_number = models.CharField(max_length=50, blank=True, verbose_name="C/L-nummer")
    breeding_class = models.CharField(max_length=6, choices=BreedingClass.choices, verbose_name="odlingsklass")
    geographies = models.ManyToManyField(Geography, blank=True, related_name="species", verbose_name="geografier")
    is_active = models.BooleanField(default=True, verbose_name="aktiv")

    objects = SpeciesQuerySet.as_manager()

    class Meta:
        ordering = ["genus__scientific_name", "scientific_name"]
        verbose_name = "art"
        verbose_name_plural = "arter"
        constraints = [models.UniqueConstraint(fields=("genus", "scientific_name"), name="unique_genus_species_scientific_name")]

    def clean(self):
        super().clean()
        errors = {}
        if self.scientific_name is not None and not self.scientific_name.strip():
            errors["scientific_name"] = "Ange ett artnamn."
        if self.common_name is not None and not self.common_name.strip():
            errors["common_name"] = "Ange ett populärnamn."
        if errors:
            raise ValidationError(errors)

    def get_species_groups(self, include_hidden=False):
        groups = SpeciesGroup.objects.filter(Q(genera=self.genus) | Q(species=self)).distinct()
        if not include_hidden:
            groups = groups.filter(is_visible=True)
        return groups

    def __str__(self):
        name = f"{self.genus} {self.scientific_name}"
        if self.cl_number:
            return f"{name} ({self.cl_number})"
        return name


class ScientificSpeciesSynonym(models.Model):
    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name="scientific_synonyms", verbose_name="art")
    scientific_name = models.CharField(max_length=200, verbose_name="vetenskapligt namn")

    class Meta:
        ordering = ["scientific_name"]
        verbose_name = "vetenskaplig synonym"
        verbose_name_plural = "vetenskapliga synonymer"
        constraints = [models.UniqueConstraint(fields=("species", "scientific_name"), name="unique_scientific_species_synonym")]

    def __str__(self):
        return self.scientific_name


class CommonNameSpeciesSynonym(models.Model):
    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name="common_name_synonyms", verbose_name="art")
    common_name = models.CharField(max_length=200, verbose_name="populärnamn")

    class Meta:
        ordering = ["common_name"]
        verbose_name = "populärnamnssynonym"
        verbose_name_plural = "populärnamnssynonymer"
        constraints = [models.UniqueConstraint(fields=("species", "common_name"), name="unique_common_name_species_synonym")]

    def __str__(self):
        return self.common_name


class SpeciesLink(models.Model):
    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name="external_links", verbose_name="art")
    url = models.URLField(max_length=500, verbose_name="URL")
    title = models.CharField(max_length=300, blank=True, verbose_name="sidtitel")
    source_name = models.CharField(max_length=100, verbose_name="källa")

    class Meta:
        ordering = ["source_name", "title", "url"]
        verbose_name = "extern artlänk"
        verbose_name_plural = "externa artlänkar"
        constraints = [models.UniqueConstraint(fields=("species", "url"), name="unique_species_external_link_url")]

    def __str__(self):
        return f"{self.source_name}: {self.title or self.url}"
