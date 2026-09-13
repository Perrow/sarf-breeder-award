from django import template

from progression.models import UserSelfmadeBadge


register = template.Library()


@register.simple_tag
def selfmade_badges_for(user):
    if not getattr(user, "is_authenticated", False):
        return UserSelfmadeBadge.objects.none()
    return (
        UserSelfmadeBadge.objects.filter(user=user)
        .select_related("badge")
        .order_by("-awarded_at", "badge__name", "pk")
    )
