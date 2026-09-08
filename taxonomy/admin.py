from django.contrib import admin

from .models import Genus, SpeciesGroup


@admin.register(Genus)
class GenusAdmin(admin.ModelAdmin):
    list_display = ("scientific_name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("scientific_name",)


@admin.register(SpeciesGroup)
class SpeciesGroupAdmin(admin.ModelAdmin):
    list_display = ("name",)
