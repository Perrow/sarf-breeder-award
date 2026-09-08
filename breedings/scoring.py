from collections import defaultdict

from associations.models import Association
from taxonomy.models import Species

from .models import AssociationCompetitionLimit, BreedingRegistration


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
    ).only("status", "awarded_breeding_class")

    return sum(
        points
        for registration in registrations
        if (points := points_for_registration(registration)) is not None
    )


def user_year_points(user, year):
    return competition_points(user, year)


def _competition_limits():
    limits = list(
        AssociationCompetitionLimit.objects.select_related("genus", "species_group")
        .prefetch_related("species_group__genera")
        .order_by("pk")
    )
    group_genus_ids = {
        limit.pk: {genus.pk for genus in limit.species_group.genera.all()}
        for limit in limits
        if limit.species_group_id
    }
    return limits, group_genus_ids


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


def association_year_scores(association, year):
    limits, group_genus_ids = _competition_limits()
    limits_by_id = {limit.pk: limit for limit in limits}
    registrations_by_user = defaultdict(list)

    registrations = BreedingRegistration.objects.filter(
        association=association,
        status=BreedingRegistration.Status.APPROVED,
        breeding_date__year=year,
    ).select_related("species__genus")

    for registration in registrations:
        points = points_for_registration(registration)
        if points is not None:
            registrations_by_user[registration.owner_id].append((registration, points))

    totals = {}
    for user_id, user_registrations in registrations_by_user.items():
        user_registrations.sort(
            key=lambda item: (-item[1], item[0].breeding_date, item[0].pk)
        )
        used_by_limit = defaultdict(int)
        total = 0
        for registration, points in user_registrations:
            matching_limit_ids = _matching_limit_ids(
                registration, limits, group_genus_ids
            )
            if any(
                used_by_limit[limit_id]
                >= limits_by_id[limit_id].max_registrations_per_member
                for limit_id in matching_limit_ids
            ):
                continue
            total += points
            for limit_id in matching_limit_ids:
                used_by_limit[limit_id] += 1
        if total:
            totals[user_id] = total

    return totals


def association_competition_points(association, year):
    return sum(association_year_scores(association, year).values())


def association_leaderboard_scores(year):
    associations = Association.objects.filter(
        breeding_registrations__status=BreedingRegistration.Status.APPROVED,
        breeding_registrations__breeding_date__year=year,
    ).distinct()

    return [
        {"association": association, "points": association_competition_points(association, year)}
        for association in associations
    ]
