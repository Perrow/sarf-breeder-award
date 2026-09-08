from django.contrib import admin

from .models import Genus, SpeciesGroup, SpeciesSynonym


@admin.register(Genus)
class GenusAdmin(admin.ModelAdmin):
    list_display = ("scientific_name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("scientific_name",)


@admin.register(SpeciesGroup)
class SpeciesGroupAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(SpeciesSynonym)
class SpeciesSynonymAdmin(admin.ModelAdmin):
    list_display = ("scientific_name", "species")
    search_fields = (
        "scientific_name",
        "species__scientific_name",
        "species__genus__scientific_name",
    )
