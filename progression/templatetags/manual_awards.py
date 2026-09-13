from django import template

from progression.models import Achievement
from progression.services import achievement_presentations_for_user


register = template.Library()


@register.simple_tag
def manual_awards_for(user):
    if not getattr(user, "is_authenticated", False):
        return []
    return [
        presentation
        for presentation in achievement_presentations_for_user(user)
        if presentation["earned"].level.achievement.achievement_type
        == Achievement.Type.MANUAL
    ]
