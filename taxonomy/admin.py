import tempfile
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlsplit

from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.core.validators import URLValidator
from django.urls import path, reverse
from django.utils.html import format_html, format_html_join

from .forms import (
    CommonNameSynonymForm,
    ScientificSynonymForm,
    SpeciesAdminForm,
    SpeciesImportForm,
    SpeciesMergeForm,
)
from .models import (
    CommonNameSpeciesSynonym,
    Geography,
    Genus,
    ScientificSpeciesSynonym,
    Species,
    SpeciesDataQuality,
    SpeciesGroup,
    SpeciesLink,
    SpeciesQualityReview,
)
from .data_quality import annotate_species_data_quality
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


class ScientificSynonymInline(admin.TabularInline):
    model = ScientificSpeciesSynonym
    form = ScientificSynonymForm
    extra = 0
    verbose_name = "vetenskaplig synonym"
    verbose_name_plural = "vetenskapliga synonymer"
    fields = ("genus_name", "species_name")


class CommonNameSynonymInline(admin.TabularInline):
    model = CommonNameSpeciesSynonym
    form = CommonNameSynonymForm
    extra = 0
    verbose_name = "populärnamnssynonym"
    verbose_name_plural = "populärnamnssynonymer"
    fields = ("common_name",)


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
    form = SpeciesAdminForm
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
        "scientific_synonyms__scientific_name",
        "common_name_synonyms__common_name",
    )
    filter_horizontal = ("geographies",)
    inlines = (ScientificSynonymInline, CommonNameSynonymInline, SpeciesLinkInline)

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

    def save_model(self, request, obj, form, change):
        synonym = form.cleaned_data.get("promote_synonym")
        if synonym is not None:
            previous = Species.objects.select_related("genus").get(pk=obj.pk)
            form.previous_scientific_name = (
                f"{previous.genus.scientific_name} {previous.scientific_name}"
            )
            obj.genus, _ = Genus.objects.get_or_create(
                scientific_name=form.promoted_genus_name
            )
            obj.scientific_name = form.promoted_scientific_name
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        synonym = form.cleaned_data.get("promote_synonym")
        if synonym is not None:
            ScientificSpeciesSynonym.objects.filter(
                pk=synonym.pk,
                species=form.instance,
            ).delete()
            ScientificSpeciesSynonym.objects.get_or_create(
                species=form.instance,
                scientific_name=form.previous_scientific_name,
            )

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


@admin.register(SpeciesDataQuality)
class SpeciesDataQualityAdmin(admin.ModelAdmin):
    """Rank species by missing catalogue metadata without editing through the proxy."""

    change_list_template = "admin/taxonomy/speciesdataquality/change_list.html"
    list_display = (
        "species_edit_link",
        "missing_count",
        "missing_swedish_name",
        "missing_english_name",
        "missing_geography",
        "missing_link",
        "review_state",
    )
    list_display_links = ()
    list_per_page = 100
    actions = None

    def get_ordering(self, request):
        # ChangeList otherwise falls back to Species.Meta.ordering, overriding
        # the score-based ordering applied in get_queryset().
        return (
            "-quality_score",
            "genus__scientific_name",
            "scientific_name",
            "pk",
        )

    def has_module_permission(self, request):
        return self.has_view_permission(request)

    def has_view_permission(self, request, obj=None):
        return (
            request.user.has_perm("taxonomy.view_species")
            or request.user.has_perm("taxonomy.change_species")
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return annotate_species_data_quality(
            self.model._default_manager.get_queryset().select_related("genus", "quality_review")
        ).order_by(
            "-quality_score", "genus__scientific_name", "scientific_name", "pk"
        )

    def changelist_view(self, request, extra_context=None):
        if not self.has_view_permission(request):
            return super().changelist_view(request, extra_context=extra_context)

        # Sum all species, not just the current page.
        totals = self.get_queryset(request).aggregate(
            total_quality_score=Sum("quality_score", default=0),
            complete_species_count=Count("pk", filter=Q(quality_score=0)),
        )
        reviews = SpeciesQualityReview.objects.aggregate(
            reviewed_species_count=Count("pk", filter=Q(status=SpeciesQualityReview.Status.REVIEWED)),
            manual_review_species_count=Count("pk", filter=Q(status=SpeciesQualityReview.Status.MANUAL_REVIEW)),
        )
        totals.update(reviews)
        totals["unreviewed_species_count"] = (
            Species.objects.count()
            - reviews["reviewed_species_count"]
            - reviews["manual_review_species_count"]
        )
        return super().changelist_view(
            request,
            extra_context={**totals, **(extra_context or {})},
        )

    @admin.display(description="Art")
    def species_edit_link(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse("admin:taxonomy_species_change", args=(obj.pk,)),
            str(obj),
        )

    @admin.display(description="Bristpoäng", ordering="quality_score")
    def missing_count(self, obj):
        return obj.quality_score

    @admin.display(boolean=True, description="Svenskt namn", ordering="swedish_name_gap")
    def missing_swedish_name(self, obj):
        return not bool(obj.swedish_name_gap)

    @admin.display(boolean=True, description="Engelskt namn", ordering="english_name_gap")
    def missing_english_name(self, obj):
        return not bool(obj.english_name_gap)

    @admin.display(boolean=True, description="Geografi", ordering="geography_gap")
    def missing_geography(self, obj):
        return not bool(obj.geography_gap)

    @admin.display(boolean=True, description="Länk", ordering="link_gap")
    def missing_link(self, obj):
        return not bool(obj.link_gap)

    @admin.display(description="Granskningsstatus")
    def review_state(self, obj):
        from django.utils import timezone

        review = getattr(obj, "quality_review", None)
        if review is None:
            return "Ej granskad"
        if review.status == SpeciesQualityReview.Status.MANUAL_REVIEW:
            return "Behöver manuell granskning"
        if review.review_again_after and review.review_again_after <= timezone.localdate():
            return "Granska igen"
        return "Granskad"


@admin.register(SpeciesQualityReview)
class SpeciesQualityReviewAdmin(admin.ModelAdmin):
    """Let administrators inspect reviews and schedule a new review."""

    list_display = ("species", "status", "reviewed_at", "review_again_after", "manual_review_comment")
    list_filter = ("status",)
    search_fields = ("species__genus__scientific_name", "species__scientific_name")
    readonly_fields = (
        "species", "reviewed_at", "review_field_results", "review_sources", "notes",
    )
    fields = (
        "species", "status", "reviewed_at", "review_again_after",
        "review_field_results", "review_sources", "notes", "manual_review_comment",
    )

    def save_model(self, request, obj, form, change):
        if change and "status" in form.changed_data:
            previous_status = (
                SpeciesQualityReview.objects.filter(pk=obj.pk)
                .values_list("status", flat=True).first()
            )
            if (
                previous_status == SpeciesQualityReview.Status.MANUAL_REVIEW
                and obj.status == SpeciesQualityReview.Status.REVIEWED
            ):
                obj.review_again_after = timezone.localdate() + timedelta(days=365)
        super().save_model(request, obj, form, change)

    def response_change(self, request, obj):
        url = request.POST.get("_add_source_url")
        if url is not None:
            # Never accept an arbitrary URL from the form: only sources
            # already recorded on this review can become species links.
            if (
                isinstance(obj.sources, list)
                and url in obj.sources
                and urlsplit(url).scheme == "https"
                and urlsplit(url).hostname
                and len(url) <= 500
            ):
                try:
                    URLValidator(schemes=["https"])(url)
                except ValidationError:
                    self.message_user(
                        request, "Ogiltig källadress.", level=messages.ERROR
                    )
                else:
                    hostname = urlsplit(url).hostname.lower().removeprefix("www.")
                    source_name = {
                        "fishbase.se": "FishBase",
                        "planetcatfish.com": "PlanetCatfish",
                        "scotcat.com": "ScotCat",
                        "ciklid.org": "NCS Artregister",
                        "zoopet.com": "Zoopet",
                    }.get(hostname, hostname[:100])
                    _, created = SpeciesLink.objects.get_or_create(
                        species=obj.species,
                        url=url,
                        defaults={"source_name": source_name},
                    )
                    self.message_user(
                        request,
                        "Källänken har lagts till på arten." if created
                        else "Källänken finns redan på arten.",
                    )
            else:
                self.message_user(
                    request, "Källänken finns inte i granskningen eller är ogiltig.",
                    level=messages.ERROR,
                )
            return redirect(
                reverse("admin:taxonomy_speciesqualityreview_change", args=[obj.pk])
            )
        return super().response_change(request, obj)

    @admin.display(description="Resultat per uppgift")
    def review_field_results(self, obj):
        labels = {
            "swedish_name": "Svenskt namn",
            "english_name": "Engelskt namn",
            "geography": "Geografi",
            "links": "Artlänkar",
        }
        statuses = {
            "found": ("Finns / verifierad", "#167347"),
            "not_found": ("Inte hittad", "#a15c00"),
            "uncertain": ("Osäker", "#ad3030"),
            "not_checked": ("Inte granskad", "#666"),
        }
        results = obj.field_results if isinstance(obj.field_results, dict) else {}
        rows = []
        for key, label in labels.items():
            status, color = statuses.get(results.get(key), ("Okänd", "#666"))
            rows.append((label, color, status))
        return format_html(
            '<div style="display:grid;grid-template-columns:max-content auto;'
            'gap:.5rem 1.5rem;align-items:center">{}</div>',
            format_html_join(
                "",
                '<strong>{}</strong><span style="color:{}">{}</span>',
                rows,
            ),
        )

    @admin.display(description="Källor")
    def review_sources(self, obj):
        sources = obj.sources if isinstance(obj.sources, list) else []
        valid_urls = [
            url for url in sources
            if isinstance(url, str)
            and urlsplit(url).scheme == "https"
            and urlsplit(url).hostname
        ]
        if not valid_urls:
            return "Inga källor"
        existing_links = set(
            obj.species.external_links.values_list("url", flat=True)
        )
        items = []
        for url in valid_urls:
            link = format_html(
                '<a href="{}" target="_blank" rel="noopener noreferrer">{}</a>',
                url, url,
            )
            if url in existing_links:
                items.append(format_html('<li>{} <span>(Finns på arten)</span></li>', link))
            else:
                button = format_html(
                    '<button type="submit" class="button" name="_add_source_url"'
                    ' value="{}">Lägg till på arten</button>',
                    url,
                )
                items.append(format_html('<li>{} {}</li>', link, button))
        return format_html(
            '<ul style="margin:0;padding-left:1.5em">{}</ul>',
            format_html_join("", "{}", ((item,) for item in items)),
        )

    def has_add_permission(self, request):
        return False
