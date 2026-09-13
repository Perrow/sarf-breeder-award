from django import template

from progression.models import Achievement, AchievementBackground, UserAchievement


register = template.Library()


@register.simple_tag
def manual_awards_for(user):
    if not getattr(user, "is_authenticated", False):
        return UserAchievement.objects.none()
    return (
        UserAchievement.objects.filter(
            user=user,
            level__achievement__achievement_type=Achievement.Type.MANUAL,
        )
        .select_related("level__achievement")
        .order_by("-achieved_at", "achievement_name", "level__order", "pk")
    )


@register.simple_tag
def lifetime_award_background():
    return AchievementBackground.lifetime()
