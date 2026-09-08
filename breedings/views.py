from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import BreedingRegistrationForm
from .models import BreedingRegistration
from .scoring import points_for_registration


def _leaderboard_year(raw_year):
    current_year = timezone.localdate().year
    if not raw_year:
        return current_year
    try:
        year = int(raw_year)
    except (TypeError, ValueError):
        return current_year
    if year < 1 or year > 9999:
        return current_year
    return year


def individual_leaderboard(request):
    current_year = timezone.localdate().year
    selected_year = _leaderboard_year(request.GET.get("year"))

    registrations = (
        BreedingRegistration.objects.filter(
            status=BreedingRegistration.Status.APPROVED,
            breeding_date__year=selected_year,
        )
        .select_related("owner")
        .only("owner", "status", "awarded_breeding_class")
    )

    totals = defaultdict(int)
    users = {}
    for registration in registrations:
        points = points_for_registration(registration)
        if points is None:
            continue
        totals[registration.owner_id] += points
        users[registration.owner_id] = registration.owner

    leaderboard = [
        {
            "user": users[user_id],
            "name": users[user_id].public_display_name(),
            "points": points,
        }
        for user_id, points in totals.items()
    ]
    leaderboard.sort(
        key=lambda row: (-row["points"], row["name"].casefold(), row["user"].pk)
    )

    available_years = {
        date.year
        for date in BreedingRegistration.objects.filter(
            status=BreedingRegistration.Status.APPROVED
        ).dates("breeding_date", "year", order="DESC")
    }
    available_years.add(current_year)
    available_years.add(selected_year)

    return render(
        request,
        "breedings/individual_leaderboard.html",
        {
            "leaderboard": leaderboard,
            "selected_year": selected_year,
            "available_years": sorted(available_years, reverse=True),
        },
    )


@login_required
def breeding_list(request):
    registrations = (
        BreedingRegistration.objects.filter(owner=request.user)
        .select_related("association", "species__genus", "reviewer")
        .order_by("-breeding_date", "-pk")
    )
    return render(request, "breedings/breeding_list.html", {"registrations": registrations})


@login_required
def breeding_detail(request, pk):
    registration = get_object_or_404(
        BreedingRegistration,
        pk=pk,
        owner=request.user,
    )
    return render(
        request,
        "breedings/breeding_detail.html",
        {"registration": registration},
    )


@login_required
def breeding_return_to_draft(request, pk):
    registration = get_object_or_404(
        BreedingRegistration,
        pk=pk,
        owner=request.user,
    )
    if request.method != "POST":
        return redirect("breeding_detail", pk=registration.pk)
    if registration.status != BreedingRegistration.Status.SUBMITTED:
        messages.error(request, "Endast en inskickad odlingsregistrering kan återgå till utkast.")
        return redirect("breeding_detail", pk=registration.pk)

    registration.status = BreedingRegistration.Status.DRAFT
    registration.submitted_at = None
    registration.save(update_fields=("status", "submitted_at"))
    messages.success(request, "Odlingsregistreringen har återställts till utkast.")
    return redirect("breeding_edit", pk=registration.pk)


@login_required
def breeding_create(request):
    return _edit_breeding(request)


@login_required
def breeding_edit(request, pk):
    registration = get_object_or_404(
        BreedingRegistration,
        pk=pk,
        owner=request.user,
        status=BreedingRegistration.Status.DRAFT,
    )
    return _edit_breeding(request, registration)


def _edit_breeding(request, registration=None):
    if request.method == "POST":
        form = BreedingRegistrationForm(request.user, request.POST, instance=registration)
        if form.is_valid():
            breeding = form.save(commit=False)
            breeding.owner = request.user
            if request.POST.get("action") == "submit":
                breeding.status = BreedingRegistration.Status.SUBMITTED
                breeding.submitted_at = timezone.now()
                message = "Odlingsregistreringen har skickats in för granskning."
            else:
                breeding.status = BreedingRegistration.Status.DRAFT
                breeding.submitted_at = None
                message = "Utkastet har sparats."
            breeding.save()
            messages.success(request, message)
            return redirect("breeding_list")
    else:
        form = BreedingRegistrationForm(request.user, instance=registration)

    return render(
        request,
        "breedings/breeding_form.html",
        {"form": form, "registration": registration},
    )
