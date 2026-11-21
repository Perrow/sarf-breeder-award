"""Shared quality-score annotations for the admin overview and API."""

from django.db.models import Case, Exists, F, IntegerField, OuterRef, Value, When
from django.db.models.functions import Concat

from .models import Species, SpeciesLink


def annotate_species_data_quality(queryset):
    """Annotate the four missing-data flags and their 0-4 total."""
    species_geographies = Species.geographies.through.objects.filter(
        species_id=OuterRef("pk")
    )
    species_links = SpeciesLink.objects.filter(species_id=OuterRef("pk"))
    return (
        queryset.annotate(
            has_geography=Exists(species_geographies),
            has_link=Exists(species_links),
        )
        .annotate(
            swedish_name_gap=Case(
                When(
                    common_name__iexact=Concat(
                        F("genus__scientific_name"),
                        Value(" "),
                        F("scientific_name"),
                    ),
                    then=Value(1),
                ),
                default=Value(0),
                output_field=IntegerField(),
            ),
            english_name_gap=Case(
                When(english_name="", then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            geography_gap=Case(
                When(has_geography=False, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            link_gap=Case(
                When(has_link=False, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
        )
        .annotate(
            quality_score=(
                F("swedish_name_gap")
                + F("english_name_gap")
                + F("geography_gap")
                + F("link_gap")
            )
        )
    )
