from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from associations.models import Association

from .forms import BreedingRegistrationForm
from .models import BreedingRegistration
from .scoring import (
    association_competition_rules,
    association_leaderboard_scores,
    association_member_year_registration_ids,
    association_year_scores,
    competition_points,
    points_for_registration,
)


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

    owner_ids = BreedingRegistration.objects.filter(
        status=BreedingRegistration.Status.APPROVED,
        breeding_date__year=selected_year,
    ).values_list("owner_id", flat=True).distinct()
    users = get_user_model().objects.filter(pk__in=owner_ids)

    leaderboard = []
    for user in users:
        points = competition_points(user, selected_year)
        if not points:
            continue
        leaderboard.append(
            {
                "user": user,
                "name": user.public_display_name(),
                "points": points,
            }
        )

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


def association_leaderboard(request):
    current_year = timezone.localdate().year
    selected_year = _leaderboard_year(request.GET.get("year"))
    leaderboard = association_leaderboard_scores(selected_year)
    leaderboard.sort(
        key=lambda row: (
            -row["points"],
            row["association"].name.casefold(),
            row["association"].pk,
        )
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
        "breedings/association_leaderboard.html",
        {
            "leaderboard": leaderboard,
            "selected_year": selected_year,
            "available_years": sorted(available_years, reverse=True),
        },
    )


def association_scoring_rules(request):
    current_year = timezone.localdate().year
    selected_year = _leaderboard_year(request.GET.get("year"))
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
        "breedings/association_scoring_rules.html",
        {
            "selected_year": selected_year,
            "available_years": sorted(available_years, reverse=True),
            "rules": association_competition_rules(selected_year),
        },
    )


def association_member_leaderboard(request, association_id):
    association = get_object_or_404(Association, pk=association_id)
    current_year = timezone.localdate().year
    selected_year = _leaderboard_year(request.GET.get("year"))
    view_mode = request.GET.get("view", "contribution")
    if view_mode not in {"contribution", "individual"}:
        view_mode = "contribution"

    contribution_by_user = association_year_scores(association, selected_year)
    members = get_user_model().objects.filter(memberships__association=association).distinct()

    leaderboard = []
    for user in members:
        contribution_points = contribution_by_user.get(user.pk, 0)
        individual_points = competition_points(user, selected_year)
        if not contribution_points and not individual_points:
            continue
        leaderboard.append(
            {
                "user": user,
                "name": user.public_display_name(),
                "contribution_points": contribution_points,
                "individual_points": individual_points,
            }
        )

    score_key = "contribution_points" if view_mode == "contribution" else "individual_points"
    leaderboard.sort(
        key=lambda row: (-row[score_key], row["name"].casefold(), row["user"].pk)
    )

    available_years = {
        date.year
        for date in BreedingRegistration.objects.filter(
            owner__memberships__association=association,
            status=BreedingRegistration.Status.APPROVED,
        ).dates("breeding_date", "year", order="DESC")
    }
    available_years.add(current_year)
    available_years.add(selected_year)

    return render(
        request,
        "breedings/association_member_leaderboard.html",
        {
            "association": association,
            "leaderboard": leaderboard,
            "selected_year": selected_year,
            "available_years": sorted(available_years, reverse=True),
            "view_mode": view_mode,
            "score_key": score_key,
        },
    )


def association_member_breeding_list(request, association_id, user_id):
    association = get_object_or_404(Association, pk=association_id)
    member = get_object_or_404(
        get_user_model().objects.filter(memberships__association=association).distinct(),
        pk=user_id,
    )
    selected_year = _leaderboard_year(request.GET.get("year"))

    list_mode = request.GET.get("list", "contribution")
    if list_mode not in {"contribution", "full"}:
        list_mode = "contribution"

    leaderboard_view = request.GET.get("leaderboard", "contribution")
    if leaderboard_view not in {"contribution", "individual"}:
        leaderboard_view = "contribution"

    registration_ids = association_member_year_registration_ids(
        association,
        member,
        selected_year,
        contribution_only=list_mode == "contribution",
    )
    registrations = (
        BreedingRegistration.objects.filter(pk__in=registration_ids)
        .select_related("species__genus")
        .order_by("-breeding_date", "-pk")
    )
    rows = [
        {
            "registration": registration,
            "points": points_for_registration(registration),
        }
        for registration in registrations
    ]

    return render(
        request,
        "breedings/association_member_breeding_list.html",
        {
            "association": association,
            "member": member,
            "member_name": member.public_display_name(),
            "rows": rows,
            "selected_year": selected_year,
            "list_mode": list_mode,
            "leaderboard_view": leaderboard_view,
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
