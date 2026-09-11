from urllib.parse import urlencode

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html

from associations.admin import is_association_admin, is_system_admin, managed_associations
from taxonomy.models import Genus, Species, SpeciesGroup

from .models import (
    AssociationCompetitionLimit,
    AssociationCompetitionSettings,
    BreedingRegistration,
    current_competition_year,
)


BREEDING_MANAGER_GROUP = "Odlingsansvarig"


BREEDING_CLASS_POINTS = {
    Species.BreedingClass.BRONZE: 1,
    Species.BreedingClass.SILVER: 2,
    Species.BreedingClass.GOLD: 3,
}


def is_breeding_manager(user):
    return user.groups.filter(name=BREEDING_MANAGER_GROUP).exists()


class ReviewDecisionForm(forms.Form):
    decision = forms.ChoiceField(
        label="Beslut",
        choices=(("approve", "Godkänn"), ("reject", "Avslå")),
    )
    review_comment = forms.CharField(
        label="Granskningskommentar",
        required=False,
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 5}),
    )


class TaxonomyResolutionForm(forms.Form):
    species = forms.ModelChoiceField(
        label="Art",
        queryset=Species.objects.all(),
    )


class AssociationCompetitionLimitAdminForm(forms.ModelForm):
    class Meta:
        model = AssociationCompetitionLimit
        fields = ("genus", "species_group", "max_registrations_per_member")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["species_group"].queryset = (
            SpeciesGroup.objects.filter(species__isnull=True, genera__isnull=False)
            .distinct()
            .order_by("name")
        )


@admin.register(AssociationCompetitionSettings)
class AssociationCompetitionSettingsAdmin(admin.ModelAdmin):
    list_display = ("effective_from_year", "default_max_registrations_per_genus")
    fields = ("default_max_registrations_per_genus",)

    def has_module_permission(self, request):
        return is_system_admin(request.user)

    def has_view_permission(self, request, obj=None):
        return is_system_admin(request.user)

    def has_add_permission(self, request):
        return (
            is_system_admin(request.user)
            and not AssociationCompetitionSettings.objects.filter(
                effective_from_year=current_competition_year()
            ).exists()
        )

    def has_change_permission(self, request, obj=None):
        if not is_system_admin(request.user):
            return False
        return obj is None or obj.effective_from_year == current_competition_year()

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if not change:
            obj.effective_from_year = current_competition_year()
        super().save_model(request, obj, form, change)


@admin.register(AssociationCompetitionLimit)
class AssociationCompetitionLimitAdmin(admin.ModelAdmin):
    form = AssociationCompetitionLimitAdminForm
    list_display = ("target", "max_registrations_per_member", "effective_from_year")
    list_filter = ("effective_from_year",)
    list_select_related = ("genus", "species_group")
    fields = ("genus", "species_group", "max_registrations_per_member")

    @admin.display(description="begränsat område")
    def target(self, obj):
        return obj.genus or obj.species_group

    def has_module_permission(self, request):
        return is_system_admin(request.user)

    def has_view_permission(self, request, obj=None):
        return is_system_admin(request.user)

    def has_add_permission(self, request):
        return is_system_admin(request.user)

    def has_change_permission(self, request, obj=None):
        if not is_system_admin(request.user):
            return False
        return obj is None or obj.effective_from_year == current_competition_year()

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if not change:
            obj.effective_from_year = current_competition_year()
        super().save_model(request, obj, form, change)


@admin.register(BreedingRegistration)
class BreedingRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "owner",
        "association",
        "species",
        "breeding_date",
        "status",
        "action_link",
    )
    list_filter = ("status", "taxonomy_needs_resolution", "association")
    search_fields = (
        "owner__email",
        "species__genus__scientific_name",
        "species__scientific_name",
        "proposed_genus_name",
        "proposed_species_name",
        "proposed_common_name",
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if is_breeding_manager(request.user):
            return queryset
        return queryset.filter(association__in=managed_associations(request.user))

    def has_module_permission(self, request):
        return (
            is_system_admin(request.user)
            or is_association_admin(request.user)
            or is_breeding_manager(request.user)
        )

    def has_view_permission(self, request, obj=None):
        if not self.has_module_permission(request):
            return False
        if is_breeding_manager(request.user):
            return True
        if obj is None:
            return True
        return managed_associations(request.user).filter(pk=obj.association_id).exists()

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:object_id>/review/",
                self.admin_site.admin_view(self.review_view),
                name="breedings_breedingregistration_review",
            ),
            path(
                "<int:object_id>/resolve-taxonomy/",
                self.admin_site.admin_view(self.resolve_taxonomy_view),
                name="breedings_breedingregistration_resolve_taxonomy",
            ),
        ]
        return custom_urls + urls

    @admin.display(description="Åtgärd")
    def action_link(self, obj):
        if obj.status != BreedingRegistration.Status.SUBMITTED:
            return "–"
        if obj.taxonomy_needs_resolution:
            url = reverse("admin:breedings_breedingregistration_resolve_taxonomy", args=[obj.pk])
            return format_html('<a href="{}">Lös taxonomi</a>', url)
        url = reverse("admin:breedings_breedingregistration_review", args=[obj.pk])
        return format_html('<a href="{}">Granska</a>', url)

    def review_view(self, request, object_id):
        registration = get_object_or_404(BreedingRegistration, pk=object_id)
        if not self.has_view_permission(request, registration):
            raise PermissionDenied
        if registration.status != BreedingRegistration.Status.SUBMITTED:
            messages.error(request, "Endast inskickade odlingsregistreringar kan granskas.")
            return redirect("admin:breedings_breedingregistration_changelist")
        if registration.taxonomy_needs_resolution or registration.species is None:
            messages.error(request, "Taxonomin måste lösas innan odlingsregistreringen kan behandlas.")
            return redirect("admin:breedings_breedingregistration_resolve_taxonomy", object_id=registration.pk)

        if request.method == "POST":
            form = ReviewDecisionForm(request.POST)
            if form.is_valid():
                decision = form.cleaned_data["decision"]
                registration.reviewer = request.user
                registration.review_comment = form.cleaned_data["review_comment"]
                if decision == "approve":
                    breeding_class = registration.species.breeding_class
                    registration.status = BreedingRegistration.Status.APPROVED
                    registration.approved_at = timezone.now()
                    registration.awarded_breeding_class = breeding_class
                    registration.awarded_points = BREEDING_CLASS_POINTS[breeding_class]
                    message = "Odlingsregistreringen har godkänts."
                else:
                    registration.status = BreedingRegistration.Status.REJECTED
                    registration.approved_at = None
                    registration.awarded_breeding_class = ""
                    registration.awarded_points = None
                    message = "Odlingsregistreringen har avslagits."
                registration.save(
                    update_fields=(
                        "reviewer",
                        "review_comment",
                        "status",
                        "approved_at",
                        "awarded_breeding_class",
                        "awarded_points",
                    )
                )
                messages.success(request, message)
                return redirect("admin:breedings_breedingregistration_changelist")
        else:
            form = ReviewDecisionForm()

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Granska odlingsregistrering",
            "registration": registration,
            "form": form,
        }
        return render(request, "admin/breedings/breedingregistration/review.html", context)

    def resolve_taxonomy_view(self, request, object_id):
        registration = get_object_or_404(BreedingRegistration, pk=object_id)
        if not self.has_view_permission(request, registration):
            raise PermissionDenied
        if registration.status != BreedingRegistration.Status.SUBMITTED:
            messages.error(request, "Endast inskickade odlingsregistreringar kan få taxonomin löst.")
            return redirect("admin:breedings_breedingregistration_changelist")
        if not registration.taxonomy_needs_resolution:
            messages.info(request, "Odlingsregistreringen har redan löst taxonomi.")
            return redirect(
                "admin:breedings_breedingregistration_review",
                object_id=registration.pk,
            )

        if request.method == "POST":
            form = TaxonomyResolutionForm(request.POST)
            if form.is_valid():
                registration.species = form.cleaned_data["species"]
                registration.save(update_fields=("species", "taxonomy_needs_resolution"))
                messages.success(request, "Taxonomin har kopplats till en registrerad art.")
                return redirect("admin:breedings_breedingregistration_review", object_id=registration.pk)
        else:
            form = TaxonomyResolutionForm()

        species_add_params = {
            "scientific_name": registration.proposed_species_name,
            "common_name": registration.proposed_common_name,
            "source_genus": registration.proposed_genus_name,
        }
        matching_genus = Genus.objects.filter(
            scientific_name=registration.proposed_genus_name
        ).first()
        if matching_genus:
            species_add_params["genus"] = matching_genus.pk

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Lös taxonomi",
            "registration": registration,
            "form": form,
            "species_add_url": f'{reverse("admin:taxonomy_species_add")}?{urlencode(species_add_params)}',
        }
        return render(request, "admin/breedings/breedingregistration/resolve_taxonomy.html", context)
