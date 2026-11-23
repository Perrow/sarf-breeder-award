from collections import defaultdict
from datetime import date, timedelta

from django.db.models import Prefetch
from django.utils import timezone

from associations.models import Association, Membership
from taxonomy.models import Species

from .models import (
    AssociationCompetitionLimit,
    AssociationCompetitionSettings,
    BreedingRegistration,
)


BREEDING_CLASS_POINTS = {
    Species.BreedingClass.BRONZE: 1,
    Species.BreedingClass.SILVER: 3,
    Species.BreedingClass.GOLD: 7,
    Species.BreedingClass.ELITE: 7,
    Species.BreedingClass.UNRATED: 1,
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


def competition_points_for_registration(registration, year):
    if registration.status != BreedingRegistration.Status.APPROVED:
        return None
    if year == timezone.localdate().year and registration.species_id:
        return points_for_breeding_class(registration.species.breeding_class)
    return points_for_registration(registration)


def _competition_settings(year):
    return (
        AssociationCompetitionSettings.objects.filter(effective_from_year__lte=year)
        .order_by("-effective_from_year", "-pk")
        .first()
    )


def competition_late_reporting_days(year):
    settings = _competition_settings(year)
    return settings.late_reporting_days if settings is not None else 30


def registration_is_timely_for_competition_year(registration, year, *, late_reporting_days=None):
    if registration.breeding_date.year != year:
        return False

    # Legacy approved rows without a submission date keep their historical result.
    if registration.submitted_at is None:
        return True

    if late_reporting_days is None:
        late_reporting_days = competition_late_reporting_days(year)
    deadline = date(year, 12, 31) + timedelta(days=late_reporting_days)
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


def _competition_registrations(queryset):
    return (
        queryset.filter(status=BreedingRegistration.Status.APPROVED, species__isnull=False)
        .select_related("species")
        .order_by()
        .only(
            "owner_id", "association_id", "species_id", "species__genus_id",
            "species__breeding_class", "status", "awarded_breeding_class",
            "breeding_date", "submitted_at",
        )
    )


def _individual_year_scores(year, queryset):
    reporting_days = competition_late_reporting_days(year)
    best_points_by_owner = defaultdict(dict)
    registrations = _competition_registrations(queryset.filter(breeding_date__year=year))
    for registration in registrations.iterator():
        if not registration_is_timely_for_competition_year(
            registration, year, late_reporting_days=reporting_days
        ):
            continue
        points = competition_points_for_registration(registration, year)
        if points is not None:
            by_species = best_points_by_owner[registration.owner_id]
            by_species[registration.species_id] = max(points, by_species.get(registration.species_id, 0))

    return {owner_id: sum(by_species.values()) for owner_id, by_species in best_points_by_owner.items()}


def individual_leaderboard_scores(year, users=None):
    queryset = BreedingRegistration.objects.all()
    if users is not None:
        queryset = queryset.filter(owner__in=users)
    return _individual_year_scores(year, queryset)


def competition_points(user, year):
    return _individual_year_scores(year, BreedingRegistration.objects.filter(owner=user)).get(user.pk, 0)


def available_competition_years(queryset):
    settings = iter(AssociationCompetitionSettings.objects.order_by("effective_from_year", "pk"))
    next_settings = next(settings, None)
    reporting_days = 30
    years = set()
    registrations = _competition_registrations(queryset).order_by("breeding_date")
    for registration in registrations.iterator():
        year = registration.breeding_date.year
        if year in years:
            continue
        while next_settings is not None and next_settings.effective_from_year <= year:
            reporting_days = next_settings.late_reporting_days
            next_settings = next(settings, None)
        if registration_is_timely_for_competition_year(
            registration, year, late_reporting_days=reporting_days
        ) and competition_points_for_registration(registration, year) is not None:
            years.add(year)
    return sorted(years, reverse=True)


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
    settings = _competition_settings(year)
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


def _association_year_results(registrations, year, limits, group_genus_ids, settings):
    limits_by_id = {limit.pk: limit for limit in limits}
    default_genus_limit = settings.default_max_registrations_per_genus if settings else None
    reporting_days = settings.late_reporting_days if settings else 30
    registrations_by_user = defaultdict(list)

    for registration in registrations:
        if not registration_is_timely_for_competition_year(
            registration, year, late_reporting_days=reporting_days
        ):
            continue
        points = competition_points_for_registration(registration, year)
        if points is not None:
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


def _association_results(association, year):
    limits, group_genus_ids = _competition_limits(year)
    registrations = _competition_registrations(
        BreedingRegistration.objects.filter(association=association, breeding_date__year=year)
    )
    return _association_year_results(registrations, year, limits, group_genus_ids, _competition_settings(year))


def association_year_scores(association, year):
    totals, _, _ = _association_results(association, year)
    return totals


def association_member_year_registration_ids(association, user, year, contribution_only):
    _, eligible_registration_ids, counted_registration_ids = _association_results(association, year)
    source = counted_registration_ids if contribution_only else eligible_registration_ids
    return source.get(user.pk, [])


def association_competition_points(association, year):
    return sum(association_year_scores(association, year).values())


def association_leaderboard_scores(year):
    registrations_by_association = defaultdict(list)
    registrations = _competition_registrations(
        BreedingRegistration.objects.filter(breeding_date__year=year)
    )
    for registration in registrations.iterator():
        registrations_by_association[registration.association_id].append(registration)
    if not registrations_by_association:
        return []

    associations = Association.objects.filter(pk__in=registrations_by_association).prefetch_related(
        Prefetch("memberships", queryset=Membership.objects.only("association_id", "user_id"))
    )
    limits, group_genus_ids = _competition_limits(year)
    settings = _competition_settings(year)

    result = []
    for association in associations:
        scores, _, _ = _association_year_results(
            registrations_by_association[association.pk], year, limits, group_genus_ids, settings
        )
        points = sum(scores.values())
        if points:
            result.append(
                {
                    "association": association,
                    "points": points,
                    "grower_count": len({
                        membership.user_id for membership in association.memberships.all()
                        if membership.user_id in scores
                    }),
                }
            )
    return result
