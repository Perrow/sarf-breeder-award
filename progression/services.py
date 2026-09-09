from breedings.models import BreedingRegistration
from breedings.scoring import points_for_registration

from .models import Achievement, AchievementRequirement, UserAchievement


def _registrations_for(user, year=None):
    queryset = BreedingRegistration.objects.filter(
        owner=user,
        status=BreedingRegistration.Status.APPROVED,
        species__isnull=False,
    ).select_related("species__genus")
    if year is not None:
        queryset = queryset.filter(breeding_date__year=year)
    return list(queryset)


def _target_species_ids(requirement):
    genus_ids = set(requirement.genera.values_list("pk", flat=True))
    groups = requirement.species_groups.prefetch_related("genera", "species").all()
    species_ids = set()
    for group in groups:
        genus_ids.update(group.genera.values_list("pk", flat=True))
        species_ids.update(group.species.values_list("pk", flat=True))
    return genus_ids, species_ids


def _matching_registrations(requirement, registrations):
    genus_ids, species_ids = _target_species_ids(requirement)
    if not genus_ids and not species_ids:
        return registrations
    return [
        registration
        for registration in registrations
        if registration.species.genus_id in genus_ids
        or registration.species_id in species_ids
    ]


def _requirement_is_met(requirement, registrations):
    matching = _matching_registrations(requirement, registrations)
    if requirement.kind == AchievementRequirement.Kind.BREEDING_COUNT:
        return len(matching) >= requirement.value

    best_points_by_species = {}
    for registration in matching:
        points = points_for_registration(registration)
        if points is None:
            continue
        best_points_by_species[registration.species_id] = max(
            points,
            best_points_by_species.get(registration.species_id, 0),
        )
    return sum(best_points_by_species.values()) >= requirement.value


def _level_is_met(level, registrations):
    requirements = list(
        level.requirements.prefetch_related(
            "genera",
            "species_groups__genera",
            "species_groups__species",
        )
    )
    return bool(requirements) and all(
        _requirement_is_met(requirement, registrations)
        for requirement in requirements
    )


def sync_achievements(user):
    achievements = Achievement.objects.prefetch_related(
        "levels__requirements__genera",
        "levels__requirements__species_groups__genera",
        "levels__requirements__species_groups__species",
    )
    all_registrations = _registrations_for(user)
    years = sorted({registration.breeding_date.year for registration in all_registrations})

    for achievement in achievements:
        evaluation_years = years if achievement.calendar_year_based else [None]
        for year in evaluation_years:
            registrations = (
                [
                    registration
                    for registration in all_registrations
                    if registration.breeding_date.year == year
                ]
                if year is not None
                else all_registrations
            )
            for level in achievement.levels.all():
                if not _level_is_met(level, registrations):
                    continue
                UserAchievement.objects.get_or_create(
                    user=user,
                    level=level,
                    calendar_year=year,
                    defaults={
                        "achievement_name": achievement.name,
                        "level_name": level.name,
                        "level_description": level.description,
                    },
                )


def achievements_for_user(user):
    sync_achievements(user)
    return list(
        user.achievements.select_related("level__achievement").order_by(
            "achievement_name",
            "calendar_year",
            "level__order",
        )
    )
