from collections import defaultdict
from datetime import date, timedelta

from django.utils import timezone

from associations.models import Association
from taxonomy.models import Species

from .models import (
    AssociationCompetitionLimit,
    AssociationCompetitionSettings,
    BreedingRegistration,
)


BREEDING_CLASS_POINTS = {
    Species.BreedingClass.BRONZE: 1,
    Species.BreedingClass.SILVER: 2,
    Species.BreedingClass.GOLD: 3,
}


def points_for_breeding_class(breeding_class):
    try:
        return BREEDING_CLASS_POINTS[breeding_class]
    except KeyError as exc:
        raise ValueError("Ogiltig odlingsklass.") from exc


def points_for_registration(registration):
    if registration.status != BreedingRegistration.Status.APPROVED:
        return None
    if not registration.awarded_breeding_class:
        return None
    return points_for_breeding_class(registration.awarded_breeding_class)


def registration_is_timely_for_competition_year(registration, year):
    if registration.breeding_date.year != year:
        return False

    if year >= timezone.localdate().year:
        return True

    # Legacy approved rows created before submitted_at was introduced keep their
    # historical result. All registrations submitted through the application
    # have submitted_at and are subject to the deadline below.
    if registration.submitted_at is None:
        return True

    deadline = date(year, 12, 31) + timedelta(days=30)
    submitted_date = timezone.localtime(registration.submitted_at).date()
    return submitted_date <= deadline


def career_points(user):
    best_points_by_species = {}
    registrations = BreedingRegistration.objects.filter(
        owner=user,
        status=BreedingRegistration.Status.APPROVED,
        species__isnull=False,
    ).only("species_id", "status", "awarded_breeding_class")

    for registration in registrations:
        points = points_for_registration(registration)
        if points is None:
            continue
        best_points_by_species[registration.species_id] = max(
            points,
            best_points_by_species.get(registration.species_id, 0),
        )

    return sum(best_points_by_species.values())


def competition_points(user, year):
    registrations = BreedingRegistration.objects.filter(
        owner=user,
        status=BreedingRegistration.Status.APPROVED,
        breeding_date__year=year,
    ).only(
        "species_id",
        "status",
        "awarded_breeding_class",
        "breeding_date",
        "submitted_at",
    )

    best_points_by_species = {}
    for registration in registrations:
        if not registration_is_timely_for_competition_year(registration, year):
            continue
        points = points_for_registration(registration)
        if points is None:
            continue
        if registration.species_id is None:
            continue
        best_points_by_species[registration.species_id] = max(
            points,
            best_points_by_species.get(registration.species_id, 0),
        )

    return sum(best_points_by_species.values())


def user_year_points(user, year):
    return competition_points(user, year)


def _competition_limits(year):
    candidates = list(
        AssociationCompetitionLimit.objects.filter(effective_from_year__lte=year)
        .select_related("genus", "species_group")
        .prefetch_related("species_group__genera")
        .order_by("-effective_from_year", "-pk")
    )
    latest_by_target = {}
    for limit in candidates:
        target = (
            ("genus", limit.genus_id)
            if limit.genus_id
            else ("species_group", limit.species_group_id)
        )
        latest_by_target.setdefault(target, limit)

    limits = list(latest_by_target.values())
    group_genus_ids = {
        limit.pk: {genus.pk for genus in limit.species_group.genera.all()}
        for limit in limits
        if limit.species_group_id
    }
    return limits, group_genus_ids


def _default_genus_limit(year):
    settings = (
        AssociationCompetitionSettings.objects.filter(effective_from_year__lte=year)
        .order_by("-effective_from_year", "-pk")
        .first()
    )
    if settings is None:
        return None
    return settings.default_max_registrations_per_genus


def association_competition_rules(year):
    limits, _ = _competition_limits(year)
    return {
        "genus_limits": sorted(
            (limit for limit in limits if limit.genus_id),
            key=lambda limit: limit.genus.scientific_name.casefold(),
        ),
        "species_group_limits": sorted(
            (limit for limit in limits if limit.species_group_id),
            key=lambda limit: limit.species_group.name.casefold(),
        ),
        "default_genus_limit": _default_genus_limit(year),
    }


def _matching_limit_ids(registration, limits, group_genus_ids):
    if not registration.species_id:
        return []
    genus_id = registration.species.genus_id
    result = []
    for limit in limits:
        if limit.genus_id == genus_id:
            result.append(limit.pk)
        elif limit.species_group_id and genus_id in group_genus_ids.get(limit.pk, set()):
            result.append(limit.pk)
    return result


def _association_year_results(association, year):
    limits, group_genus_ids = _competition_limits(year)
    limits_by_id = {limit.pk: limit for limit in limits}
    default_genus_limit = _default_genus_limit(year)
    registrations_by_user = defaultdict(list)

    registrations = (
        BreedingRegistration.objects.filter(
            association=association,
            status=BreedingRegistration.Status.APPROVED,
            breeding_date__year=year,
        )
        .select_related("species__genus")
        .only(
            "owner_id",
            "species_id",
            "species__genus_id",
            "status",
            "awarded_breeding_class",
            "breeding_date",
            "submitted_at",
        )
    )

    for registration in registrations:
        if not registration_is_timely_for_competition_year(registration, year):
            continue
        points = points_for_registration(registration)
        if points is not None and registration.species_id is not None:
            registrations_by_user[registration.owner_id].append((registration, points))

    totals = {}
    eligible_registration_ids = defaultdict(list)
    counted_registration_ids = defaultdict(list)

    for user_id, user_registrations in registrations_by_user.items():
        user_registrations.sort(
            key=lambda item: (-item[1], item[0].breeding_date, item[0].pk)
        )
        used_by_limit = defaultdict(int)
        counted_species = set()
        total = 0

        for registration, points in user_registrations:
            if registration.species_id in counted_species:
                continue
            counted_species.add(registration.species_id)
            eligible_registration_ids[user_id].append(registration.pk)

            matching_limit_ids = _matching_limit_ids(
                registration, limits, group_genus_ids
            )

            if matching_limit_ids:
                if any(
                    used_by_limit[("specific", limit_id)]
                    >= limits_by_id[limit_id].max_registrations_per_member
                    for limit_id in matching_limit_ids
                ):
                    continue
                total += points
                counted_registration_ids[user_id].append(registration.pk)
                for limit_id in matching_limit_ids:
                    used_by_limit[("specific", limit_id)] += 1
                continue

            if default_genus_limit is not None:
                default_key = ("default_genus", registration.species.genus_id)
                if used_by_limit[default_key] >= default_genus_limit:
                    continue
                used_by_limit[default_key] += 1

            total += points
            counted_registration_ids[user_id].append(registration.pk)

        if total:
            totals[user_id] = total

    return totals, dict(eligible_registration_ids), dict(counted_registration_ids)


def association_year_scores(association, year):
    totals, _, _ = _association_year_results(association, year)
    return totals


def association_member_year_registration_ids(association, user, year, contribution_only):
    _, eligible_registration_ids, counted_registration_ids = _association_year_results(
        association, year
    )
    source = counted_registration_ids if contribution_only else eligible_registration_ids
    return source.get(user.pk, [])


def association_competition_points(association, year):
    return sum(association_year_scores(association, year).values())


def association_leaderboard_scores(year):
    associations = Association.objects.filter(
        breeding_registrations__status=BreedingRegistration.Status.APPROVED,
        breeding_registrations__breeding_date__year=year,
    ).distinct()

    result = []
    for association in associations:
        scores = association_year_scores(association, year)
        points = sum(scores.values())
        if not points:
            continue
        member_ids = set(association.memberships.values_list("user_id", flat=True))
        grower_count = len(member_ids.intersection(scores.keys()))
        result.append(
            {
                "association": association,
                "points": points,
                "grower_count": grower_count,
            }
        )
    return result
