from django import template

from progression.models import Achievement, UserAchievement


register = template.Library()


@register.simple_tag
def selfmade_badges_for(user):
    if not getattr(user, "is_authenticated", False):
        return UserAchievement.objects.none()
    return (
        UserAchievement.objects.filter(
            user=user,
            level__achievement__achievement_type=Achievement.Type.SELFMADE,
        )
        .select_related("level__achievement")
        .order_by("-achieved_at", "achievement_name", "level__order", "pk")
    )
