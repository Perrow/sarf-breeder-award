from django.contrib import admin

from .models import BreedingRegistration


@admin.register(BreedingRegistration)
class BreedingRegistrationAdmin(admin.ModelAdmin):
    list_display = ("owner", "association", "species", "breeding_date", "status", "taxonomy_needs_resolution")
    list_filter = ("status", "taxonomy_needs_resolution", "association")
    search_fields = (
        "owner__email",
        "species__genus__scientific_name",
        "species__scientific_name",
        "proposed_genus_name",
        "proposed_species_name",
        "proposed_common_name",
    )
