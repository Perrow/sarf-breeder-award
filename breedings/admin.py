from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html

from associations.admin import is_association_admin, is_system_admin, managed_associations
from taxonomy.models import Species

from .models import BreedingRegistration


BREEDING_CLASS_POINTS = {
    Species.BreedingClass.BRONZE: 1,
    Species.BreedingClass.SILVER: 2,
    Species.BreedingClass.GOLD: 3,
}


class ReviewDecisionForm(forms.Form):
    decision = forms.ChoiceField(
        label="Beslut",
        choices=(("approve", "Godkänn"), ("reject", "Avslå")),
    )
    awarded_breeding_class = forms.ChoiceField(
        label="Tilldelad odlingsklass",
        choices=(("", "---------"), *Species.BreedingClass.choices),
        required=False,
    )
    review_comment = forms.CharField(
        label="Granskningskommentar",
        required=False,
        widget=forms.Textarea(attrs={"rows": 5}),
    )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("decision") == "approve" and not cleaned_data.get("awarded_breeding_class"):
            self.add_error("awarded_breeding_class", "Välj odlingsklass för en godkänd odling.")
        return cleaned_data


@admin.register(BreedingRegistration)
class BreedingRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "owner",
        "association",
        "species",
        "breeding_date",
        "status",
        "taxonomy_needs_resolution",
        "review_link",
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
        return super().get_queryset(request).filter(association__in=managed_associations(request.user))

    def has_module_permission(self, request):
        return is_system_admin(request.user) or is_association_admin(request.user)

    def has_view_permission(self, request, obj=None):
        if not self.has_module_permission(request):
            return False
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
        ]
        return custom_urls + urls

    @admin.display(description="Granskning")
    def review_link(self, obj):
        if obj.status != BreedingRegistration.Status.SUBMITTED:
            return "–"
        url = reverse("admin:breedings_breedingregistration_review", args=[obj.pk])
        return format_html('<a href="{}">Granska</a>', url)

    def review_view(self, request, object_id):
        registration = get_object_or_404(BreedingRegistration, pk=object_id)
        if not self.has_view_permission(request, registration):
            raise PermissionDenied
        if registration.status != BreedingRegistration.Status.SUBMITTED:
            messages.error(request, "Endast inskickade odlingsregistreringar kan granskas.")
            return redirect("admin:breedings_breedingregistration_changelist")

        if request.method == "POST":
            form = ReviewDecisionForm(request.POST)
            if form.is_valid():
                decision = form.cleaned_data["decision"]
                registration.reviewer = request.user
                registration.review_comment = form.cleaned_data["review_comment"]
                if decision == "approve":
                    breeding_class = form.cleaned_data["awarded_breeding_class"]
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
