from django import template

from progression.models import UserDeMeritBadge


register = template.Library()


@register.simple_tag
def demerit_badges_for(user):
    if not getattr(user, "is_authenticated", False):
        return UserDeMeritBadge.objects.none()
    return (
        UserDeMeritBadge.objects.filter(user=user)
        .select_related("badge")
        .order_by("-awarded_at", "badge__name", "pk")
    )
