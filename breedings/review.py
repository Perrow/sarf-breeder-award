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
    show_on_species_page = forms.BooleanField(
        label="Visa odlingsrapporten på artsidan",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    species_page_display_name = forms.CharField(
        label="Visningsnamn",
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, registration=None, publication_only=False, **kwargs):
        self.registration = registration
        self.publication_only = publication_only
        super().__init__(*args, **kwargs)
        if registration is not None and not self.is_bound:
            self.initial.update(
                {
                    "review_comment": registration.review_comment,
                    "show_on_species_page": registration.show_on_species_page,
                    "species_page_display_name": registration.species_page_display_name,
                }
            )
        if publication_only:
            self.fields.pop("review_comment")

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("show_on_species_page"):
            if self.registration is None or self.registration.species_id is None:
                self.add_error(
                    "show_on_species_page",
                    "Rapporten måste vara kopplad till en registrerad art för att kunna visas på artsidan.",
                )
            if not (cleaned_data.get("species_page_display_name") or "").strip():
                self.add_error(
                    "species_page_display_name",
                    "Ange ett visningsnamn när rapporten ska visas på artsidan.",
                )
        return cleaned_data


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


def _save_publication(registration, form):
    registration.show_on_species_page = form.cleaned_data["show_on_species_page"]
    registration.species_page_display_name = (
        form.cleaned_data["species_page_display_name"].strip()
    )
    registration.save(
        update_fields=("show_on_species_page", "species_page_display_name")
    )


@login_required
def review_list(request):
    _require_review_access(request.user)
    available = reviewable_registrations(request.user).select_related(
        "owner", "association", "species__genus"
    )
    registrations = available.filter(
        status=BreedingRegistration.Status.SUBMITTED
    ).order_by("breeding_date", "pk")
    approved_registrations = available.filter(
        status=BreedingRegistration.Status.APPROVED
    ).order_by("-breeding_date", "-pk")
    return render(
        request,
        "breedings/review_list.html",
        {
            "registrations": registrations,
            "approved_registrations": approved_registrations,
        },
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

    if registration.status not in {
        BreedingRegistration.Status.SUBMITTED,
        BreedingRegistration.Status.APPROVED,
    }:
        messages.error(
            request,
            "Endast inskickade eller godkända odlingsregistreringar kan hanteras här.",
        )
        return redirect("breeding_review_list")

    if (
        registration.status == BreedingRegistration.Status.SUBMITTED
        and (registration.taxonomy_needs_resolution or registration.species is None)
    ):
        messages.error(
            request,
            "Taxonomin måste lösas innan odlingsregistreringen kan behandlas.",
        )
        return redirect("breeding_review_taxonomy", pk=registration.pk)

    publication_only = registration.status == BreedingRegistration.Status.APPROVED

    if request.method == "POST":
        form = ReviewDecisionForm(
            request.POST,
            registration=registration,
            publication_only=publication_only,
        )

        if publication_only:
            action = "publication" if "save_publication" in request.POST else None
            if action is None:
                form.add_error(None, "Spara publiceringsinställningarna med knappen Spara.")
        elif "approve" in request.POST:
            action = "approve"
        elif "reject" in request.POST:
            action = "reject"
        elif "save_without_decision" in request.POST:
            action = "save"
        else:
            action = None
            form.add_error(None, "Välj Godkänn, Avslå eller Spara utan beslut.")

        if (
            not publication_only
            and action != "approve"
            and form.data.get("show_on_species_page")
        ):
            form.add_error(
                "show_on_species_page",
                "Rapporten kan publiceras på artsidan när den godkänns.",
            )

        if form.is_valid():
            if publication_only:
                _save_publication(registration, form)
                messages.success(request, "Publiceringsinställningarna har sparats.")
                return redirect("breeding_review_list")

            registration.reviewer = request.user
            registration.review_comment = form.cleaned_data["review_comment"]

            if action == "approve":
                breeding_class = registration.species.breeding_class
                registration.status = BreedingRegistration.Status.APPROVED
                registration.approved_at = timezone.now()
                registration.awarded_breeding_class = breeding_class
                registration.awarded_points = BREEDING_CLASS_POINTS[breeding_class]
                registration.show_on_species_page = form.cleaned_data[
                    "show_on_species_page"
                ]
                registration.species_page_display_name = (
                    form.cleaned_data["species_page_display_name"].strip()
                )
                registration.save(
                    update_fields=(
                        "reviewer",
                        "review_comment",
                        "status",
                        "approved_at",
                        "awarded_breeding_class",
                        "awarded_points",
                        "show_on_species_page",
                        "species_page_display_name",
                    )
                )
                messages.success(request, "Odlingsregistreringen har godkänts.")
            elif action == "reject":
                registration.status = BreedingRegistration.Status.REJECTED
                registration.approved_at = None
                registration.awarded_breeding_class = ""
                registration.awarded_points = None
                registration.show_on_species_page = False
                registration.save(
                    update_fields=(
                        "reviewer",
                        "review_comment",
                        "status",
                        "approved_at",
                        "awarded_breeding_class",
                        "awarded_points",
                        "show_on_species_page",
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
            registration=registration,
            publication_only=publication_only,
        )

    return render(
        request,
        "breedings/review_registration.html",
        {
            "registration": registration,
            "form": form,
            "publication_only": publication_only,
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
