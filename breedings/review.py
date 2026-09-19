from urllib.parse import urlencode

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from associations.admin import is_association_admin, is_system_admin, managed_associations
from taxonomy.models import Genus, Species

from .models import BreedingRegistration
from .scoring import BREEDING_CLASS_POINTS


BREEDING_REVIEWER_GROUP = "Odlingsgranskare"


def is_breeding_reviewer(user):
    return (
        getattr(user, "is_authenticated", False)
        and user.groups.filter(name=BREEDING_REVIEWER_GROUP).exists()
    )


def reviewable_registrations(user):
    queryset = BreedingRegistration.objects.all()
    if is_system_admin(user) or is_breeding_reviewer(user):
        return queryset
    if is_association_admin(user):
        return queryset.filter(association__in=managed_associations(user))
    return queryset.none()


def can_review_breedings(user):
    return (
        is_system_admin(user)
        or is_breeding_reviewer(user)
        or is_association_admin(user)
    )


def can_review_registration(user, registration):
    return reviewable_registrations(user).filter(pk=registration.pk).exists()


class ReviewDecisionForm(forms.Form):
    review_comment = forms.CharField(
        label="Granskningskommentar",
        required=False,
        max_length=2000,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 6,
            }
        ),
    )


class TaxonomyResolutionForm(forms.Form):
    species = forms.ModelChoiceField(
        label="Art",
        queryset=Species.objects.all(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )


def _require_review_access(user, registration=None):
    allowed = (
        can_review_breedings(user)
        if registration is None
        else can_review_registration(user, registration)
    )
    if not allowed:
        raise PermissionDenied


@login_required
def review_list(request):
    _require_review_access(request.user)
    registrations = (
        reviewable_registrations(request.user)
        .filter(status=BreedingRegistration.Status.SUBMITTED)
        .select_related("owner", "association", "species__genus")
        .order_by("breeding_date", "pk")
    )
    return render(
        request,
        "breedings/review_list.html",
        {"registrations": registrations},
    )


@login_required
def review_registration(request, pk):
    registration = get_object_or_404(
        BreedingRegistration.objects.select_related(
            "owner", "association", "species__genus"
        ).prefetch_related("species__external_links"),
        pk=pk,
    )
    _require_review_access(request.user, registration)

    if registration.status != BreedingRegistration.Status.SUBMITTED:
        messages.error(request, "Endast inskickade odlingsregistreringar kan granskas.")
        return redirect("breeding_review_list")

    if registration.taxonomy_needs_resolution or registration.species is None:
        messages.error(
            request,
            "Taxonomin måste lösas innan odlingsregistreringen kan behandlas.",
        )
        return redirect("breeding_review_taxonomy", pk=registration.pk)

    if request.method == "POST":
        form = ReviewDecisionForm(request.POST)
        if "approve" in request.POST:
            action = "approve"
        elif "reject" in request.POST:
            action = "reject"
        elif "save_without_decision" in request.POST:
            action = "save"
        else:
            action = None
            form.add_error(None, "Välj Godkänn, Avslå eller Spara utan beslut.")

        if form.is_valid():
            registration.reviewer = request.user
            registration.review_comment = form.cleaned_data["review_comment"]

            if action == "approve":
                breeding_class = registration.species.breeding_class
                registration.status = BreedingRegistration.Status.APPROVED
                registration.approved_at = timezone.now()
                registration.awarded_breeding_class = breeding_class
                registration.awarded_points = BREEDING_CLASS_POINTS[breeding_class]
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
                messages.success(request, "Odlingsregistreringen har godkänts.")
            elif action == "reject":
                registration.status = BreedingRegistration.Status.REJECTED
                registration.approved_at = None
                registration.awarded_breeding_class = ""
                registration.awarded_points = None
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
                messages.success(request, "Odlingsregistreringen har avslagits.")
            else:
                registration.save(update_fields=("reviewer", "review_comment"))
                messages.success(
                    request,
                    "Granskningsuppgifterna har sparats utan beslut.",
                )
            return redirect("breeding_review_list")
    else:
        form = ReviewDecisionForm(
            initial={"review_comment": registration.review_comment}
        )

    return render(
        request,
        "breedings/review_registration.html",
        {
            "registration": registration,
            "form": form,
        },
    )


@login_required
def resolve_taxonomy(request, pk):
    registration = get_object_or_404(BreedingRegistration, pk=pk)
    _require_review_access(request.user, registration)

    if registration.status != BreedingRegistration.Status.SUBMITTED:
        messages.error(
            request,
            "Endast inskickade odlingsregistreringar kan få taxonomin löst.",
        )
        return redirect("breeding_review_list")

    if not registration.taxonomy_needs_resolution:
        messages.info(request, "Odlingsregistreringen har redan löst taxonomi.")
        return redirect("breeding_review", pk=registration.pk)

    if request.method == "POST":
        form = TaxonomyResolutionForm(request.POST)
        if form.is_valid():
            registration.species = form.cleaned_data["species"]
            registration.save(update_fields=("species", "taxonomy_needs_resolution"))
            messages.success(
                request,
                "Taxonomin har kopplats till en registrerad art.",
            )
            return redirect("breeding_review", pk=registration.pk)
    else:
        form = TaxonomyResolutionForm()

    species_add_url = None
    if request.user.is_staff and request.user.has_perm("taxonomy.add_species"):
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
        species_add_url = (
            f'{reverse("admin:taxonomy_species_add")}?{urlencode(species_add_params)}'
        )

    return render(
        request,
        "breedings/review_taxonomy.html",
        {
            "registration": registration,
            "form": form,
            "species_add_url": species_add_url,
        },
    )
