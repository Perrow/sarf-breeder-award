import tempfile
from pathlib import Path

from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils.html import format_html

from .forms import SpeciesImportForm, SpeciesMergeForm
from .models import Geography, Genus, Species, SpeciesGroup, SpeciesLink, SpeciesSynonym
from .species_import import SpeciesImportError, import_species_file
from .species_merge import merge_species


@admin.register(Genus)
class GenusAdmin(admin.ModelAdmin):
    list_display = ("scientific_name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("scientific_name",)


@admin.register(Geography)
class GeographyAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(SpeciesGroup)
class SpeciesGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "is_visible")
    list_filter = ("is_visible",)
    search_fields = ("name",)
    filter_horizontal = ("genera", "species")


class SpeciesSynonymInline(admin.TabularInline):
    model = SpeciesSynonym
    extra = 0


class SpeciesLinkInline(admin.TabularInline):
    model = SpeciesLink
    extra = 0
    fields = ("link_preview", "source_name", "title", "url")
    readonly_fields = ("link_preview",)

    @admin.display(description="Länk")
    def link_preview(self, obj):
        if not obj or not obj.url:
            return "–"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener">{}</a> ({})',
            obj.url,
            obj.title or obj.url,
            obj.source_name,
        )


@admin.register(Species)
class SpeciesAdmin(admin.ModelAdmin):
    change_list_template = "admin/taxonomy/species/change_list.html"
    change_form_template = "admin/taxonomy/species/change_form.html"
    list_display = (
        "genus",
        "scientific_name",
        "common_name",
        "geography_names",
        "group_names",
        "breeding_class",
        "is_active",
    )
    list_filter = ("is_active", "breeding_class", "genus", "geographies")
    search_fields = (
        "scientific_name",
        "genus__scientific_name",
        "common_name",
        "english_name",
        "synonyms__scientific_name",
        "synonyms__common_name",
    )
    filter_horizontal = ("geographies",)
    inlines = (SpeciesSynonymInline, SpeciesLinkInline)

    def get_urls(self):
        return [
            path(
                "import/help/",
                self.admin_site.admin_view(self.import_species_help_view),
                name="taxonomy_species_import_help",
            ),
            path(
                "import/",
                self.admin_site.admin_view(self.import_species_view),
                name="taxonomy_species_import",
            ),
            path(
                "<path:object_id>/merge/",
                self.admin_site.admin_view(self.merge_species_view),
                name="taxonomy_species_merge",
            ),
        ] + super().get_urls()

    def _check_import_permission(self, request):
        if not self.has_change_permission(request):
            raise PermissionDenied

    def import_species_help_view(self, request):
        self._check_import_permission(request)
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Dokumentation för artimport",
            "species_import_url": reverse("admin:taxonomy_species_import"),
            "species_changelist_url": reverse("admin:taxonomy_species_changelist"),
        }
        return render(request, "admin/taxonomy/species/import_help.html", context)

    def import_species_view(self, request):
        self._check_import_permission(request)

        stats = None
        import_error = None
        form = SpeciesImportForm(request.POST or None, request.FILES or None)
        if request.method == "POST" and form.is_valid():
            uploaded_file = form.cleaned_data["import_file"]
            temporary_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temporary_file:
                    for chunk in uploaded_file.chunks():
                        temporary_file.write(chunk)
                    temporary_path = Path(temporary_file.name)
                stats = import_species_file(temporary_path)
                form = SpeciesImportForm()
            except SpeciesImportError as exc:
                import_error = str(exc)
            finally:
                if temporary_path is not None:
                    temporary_path.unlink(missing_ok=True)

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Importera arter",
            "form": form,
            "stats": stats,
            "import_error": import_error,
            "species_changelist_url": reverse("admin:taxonomy_species_changelist"),
            "species_import_help_url": reverse("admin:taxonomy_species_import_help"),
        }
        return render(request, "admin/taxonomy/species/import.html", context)

    def merge_species_view(self, request, object_id):
        source = get_object_or_404(Species.objects.select_related("genus"), pk=object_id)
        if not self.has_delete_permission(request, source) or not self.has_change_permission(request, source):
            raise PermissionDenied

        form = SpeciesMergeForm(request.POST or None, source_species=source)
        if request.method == "POST" and form.is_valid():
            target = form.cleaned_data["target_species"]
            merge_species(source, target)
            self.message_user(
                request,
                f"Arten slogs ihop med {target}.",
                level=messages.SUCCESS,
            )
            return redirect("admin:taxonomy_species_change", target.pk)

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": f"Slå ihop {source}",
            "source": source,
            "form": form,
            "change_url": reverse("admin:taxonomy_species_change", args=(source.pk,)),
        }
        return render(request, "admin/taxonomy/species/merge.html", context)

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change, **kwargs)
        source_genus = request.GET.get("source_genus", "").strip()
        if obj is None and source_genus and not request.GET.get("genus"):
            form.base_fields["genus"].help_text = f"Användaren angav släkte: {source_genus}"
        return form

    @admin.display(description="geografier")
    def geography_names(self, obj):
        return ", ".join(obj.geographies.values_list("name", flat=True))

    @admin.display(description="artgrupper")
    def group_names(self, obj):
        return ", ".join(
            obj.get_species_groups(include_hidden=True).values_list("name", flat=True)
        )


@admin.register(SpeciesSynonym)
class SpeciesSynonymAdmin(admin.ModelAdmin):
    list_display = ("scientific_name", "species")
    search_fields = (
        "scientific_name",
        "common_name",
        "species__scientific_name",
        "species__common_name",
        "species__genus__scientific_name",
    )
