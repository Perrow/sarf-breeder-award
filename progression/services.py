from breedings.scoring import career_points

from .models import LevelDefinition, UserLevelAchievement


def sync_level_achievements(user):
    points = career_points(user)
    earned_levels = LevelDefinition.objects.filter(points_required__lte=points).order_by("points_required", "name")
    for level in earned_levels:
        UserLevelAchievement.objects.get_or_create(
            user=user,
            level=level,
            defaults={
                "level_name": level.name,
                "points_required": level.points_required,
            },
        )
    return points


def progression_for_user(user):
    points = sync_level_achievements(user)
    achievements = list(user.level_achievements.order_by("points_required", "achieved_at"))
    current_level = max(achievements, key=lambda achievement: achievement.points_required, default=None)
    return points, current_level, achievements
