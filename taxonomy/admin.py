from django.contrib import admin

from .models import Genus, Species, SpeciesGroup, SpeciesSynonym


@admin.register(Genus)
class GenusAdmin(admin.ModelAdmin):
    list_display = ("scientific_name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("scientific_name",)


@admin.register(SpeciesGroup)
class SpeciesGroupAdmin(admin.ModelAdmin):
    list_display = ("name",)


class SpeciesSynonymInline(admin.TabularInline):
    model = SpeciesSynonym
    extra = 0


@admin.register(Species)
class SpeciesAdmin(admin.ModelAdmin):
    list_display = (
        "genus",
        "scientific_name",
        "common_name",
        "species_group",
        "breeding_class",
        "is_active",
    )
    list_filter = ("is_active", "species_group", "breeding_class", "genus")
    search_fields = (
        "scientific_name",
        "genus__scientific_name",
        "common_name",
        "english_name",
        "synonyms__scientific_name",
    )
    inlines = (SpeciesSynonymInline,)


@admin.register(SpeciesSynonym)
class SpeciesSynonymAdmin(admin.ModelAdmin):
    list_display = ("scientific_name", "species")
    search_fields = (
        "scientific_name",
        "species__scientific_name",
        "species__genus__scientific_name",
    )
