from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Achievement, AchievementBackground, AchievementLevel
from .services import remove_selfmade_level, select_selfmade_level


@login_required
def selfmade_badges(request):
    levels = (
        AchievementLevel.objects.filter(
            achievement__achievement_type=Achievement.Type.SELFMADE,
            achievement__active=True,
        )
        .select_related("achievement")
        .order_by("achievement__name", "order", "name")
    )
    selected_level_ids = set(
        request.user.achievements.filter(
            level__achievement__achievement_type=Achievement.Type.SELFMADE,
        ).values_list("level_id", flat=True)
    )
    return render(
        request,
        "progression/selfmade_badges.html",
        {
            "levels": levels,
            "selected_level_ids": selected_level_ids,
            "award_background": AchievementBackground.lifetime(),
        },
    )


@login_required
@require_POST
def award_selfmade_badge(request, level_id):
    level = get_object_or_404(
        AchievementLevel.objects.select_related("achievement"),
        pk=level_id,
        achievement__achievement_type=Achievement.Type.SELFMADE,
        achievement__active=True,
    )
    try:
        _, created = select_selfmade_level(request.user, level)
    except ValidationError:
        return redirect("selfmade_badges")
    if created:
        messages.success(request, f"Du har valt {level.achievement.name} – {level.name}.")
    else:
        messages.info(request, f"Du har redan valt {level.achievement.name} – {level.name}.")
    return redirect("selfmade_badges")


@login_required
@require_POST
def remove_selfmade_badge(request, level_id):
    level = get_object_or_404(
        AchievementLevel.objects.select_related("achievement"),
        pk=level_id,
        achievement__achievement_type=Achievement.Type.SELFMADE,
    )
    try:
        deleted = remove_selfmade_level(request.user, level)
    except ValidationError:
        return redirect("selfmade_badges")
    if deleted:
        messages.success(request, f"Du har tagit bort {level.achievement.name} – {level.name}.")
    else:
        messages.info(request, f"Du hade inte valt {level.achievement.name} – {level.name}.")
    return redirect("selfmade_badges")
