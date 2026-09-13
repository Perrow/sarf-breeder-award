from django import template

from progression.models import UserManualAward


register = template.Library()


@register.simple_tag
def manual_awards_for(user):
    if not getattr(user, "is_authenticated", False):
        return UserManualAward.objects.none()
    return UserManualAward.objects.filter(user=user).select_related("award").order_by("-awarded_on", "award__name", "pk")
