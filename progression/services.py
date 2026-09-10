from django.db import transaction
from django.utils import timezone

from breedings.models import BreedingRegistration
from breedings.scoring import points_for_registration

from .models import Achievement, AchievementBackground, AchievementRequirement, UserAchievement


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
    if requirement.kind == AchievementRequirement.Kind.SPECIES_COUNT:
        return len({registration.species_id for registration in matching}) >= requirement.value

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


def _expected_achievement_keys(achievement, registrations):
    years = sorted({registration.breeding_date.year for registration in registrations})
    evaluation_years = years if achievement.calendar_year_based else [None]
    expected = set()

    levels = list(
        achievement.levels.prefetch_related(
            "requirements__genera",
            "requirements__species_groups__genera",
            "requirements__species_groups__species",
        )
    )
    for year in evaluation_years:
        period_registrations = (
            [
                registration
                for registration in registrations
                if registration.breeding_date.year == year
            ]
            if year is not None
            else registrations
        )
        for level in levels:
            if _level_is_met(level, period_registrations):
                expected.add((level.pk, year))
    return expected, {level.pk: level for level in levels}


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


@transaction.atomic
def revalidate_achievement(achievement):
    existing_queryset = UserAchievement.objects.filter(level__achievement=achievement)
    user_ids = set(existing_queryset.values_list("user_id", flat=True))
    user_ids.update(
        BreedingRegistration.objects.filter(
            status=BreedingRegistration.Status.APPROVED,
            species__isnull=False,
        ).values_list("owner_id", flat=True).distinct()
    )

    removed = 0
    created = 0
    for user_id in user_ids:
        registrations = list(
            BreedingRegistration.objects.filter(
                owner_id=user_id,
                status=BreedingRegistration.Status.APPROVED,
                species__isnull=False,
            ).select_related("species__genus")
        )
        expected, levels_by_id = _expected_achievement_keys(achievement, registrations)
        existing = {
            (earned.level_id, earned.calendar_year): earned
            for earned in existing_queryset.filter(user_id=user_id)
        }

        invalid_ids = [
            earned.pk
            for key, earned in existing.items()
            if key not in expected
        ]
        if invalid_ids:
            deleted, _ = UserAchievement.objects.filter(pk__in=invalid_ids).delete()
            removed += deleted

        for level_id, year in expected - set(existing):
            level = levels_by_id[level_id]
            UserAchievement.objects.create(
                user_id=user_id,
                level=level,
                achievement_name=achievement.name,
                level_name=level.name,
                level_description=level.description,
                calendar_year=year,
            )
            created += 1

    return {"removed": removed, "created": created}


def achievements_for_user(user):
    sync_achievements(user)
    return list(
        user.achievements.select_related("level__achievement").order_by(
            "achievement_name",
            "calendar_year",
            "level__order",
        )
    )


def _presentation_for(earned):
    fallback_background = (
        AchievementBackground.for_year(earned.calendar_year)
        if earned.calendar_year is not None
        else AchievementBackground.lifetime()
    )
    achievement = earned.level.achievement
    custom_background = achievement.background_image if achievement.background_image else None
    return {
        "earned": earned,
        "background": fallback_background,
        "background_image": (
            custom_background
            if custom_background
            else fallback_background.image if fallback_background else None
        ),
        "background_tint": (
            fallback_background.tint_color
            if earned.calendar_year is not None and fallback_background
            else ""
        ),
        "overlay": achievement.image if achievement.image else None,
    }


def achievement_presentations_for_user(user):
    return [_presentation_for(earned) for earned in achievements_for_user(user)]


def _highest_level_per_achievement(earned):
    highest = {}
    for item in earned:
        achievement_id = item.level.achievement_id
        current = highest.get(achievement_id)
        if current is None or (item.level.order, item.pk) > (current.level.order, current.pk):
            highest[achievement_id] = item
    return list(highest.values())


def latest_achievement_presentations_for_user(user, limit=6):
    current_year = timezone.localdate().year
    earned = achievements_for_user(user)
    yearly = _highest_level_per_achievement(
        item for item in earned if item.calendar_year == current_year
    )
    career = _highest_level_per_achievement(
        item for item in earned if item.calendar_year is None
    )
    yearly.sort(key=lambda item: (item.achieved_at, item.pk), reverse=True)
    career.sort(key=lambda item: (item.achieved_at, item.pk), reverse=True)
    return {
        "year": current_year,
        "yearly": [_presentation_for(item) for item in yearly[:limit]],
        "career": [_presentation_for(item) for item in career[:limit]],
    }


def all_achievement_presentations_for_user(user):
    earned = achievements_for_user(user)
    earned.sort(key=lambda item: (item.achieved_at, item.pk), reverse=True)

    career = [_presentation_for(item) for item in earned if item.calendar_year is None]
    yearly_by_year = {}
    for item in earned:
        if item.calendar_year is None:
            continue
        yearly_by_year.setdefault(item.calendar_year, []).append(_presentation_for(item))

    yearly = [
        {"year": year, "achievements": yearly_by_year[year]}
        for year in sorted(yearly_by_year, reverse=True)
    ]
    return {"career": career, "yearly": yearly}
