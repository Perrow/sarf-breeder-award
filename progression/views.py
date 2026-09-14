from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import AchievementBackground, SelfmadeBadge, UserSelfmadeBadge


@login_required
def selfmade_badges(request):
    badges = SelfmadeBadge.objects.filter(active=True).order_by("name")
    awarded_badge_ids = set(
        UserSelfmadeBadge.objects.filter(user=request.user).values_list("badge_id", flat=True)
    )
    award_background = AchievementBackground.lifetime()
    return render(
        request,
        "progression/selfmade_badges.html",
        {
            "badges": badges,
            "awarded_badge_ids": awarded_badge_ids,
            "award_background": award_background,
        },
    )


@login_required
@require_POST
def award_selfmade_badge(request, badge_id):
    badge = get_object_or_404(SelfmadeBadge, pk=badge_id, active=True)
    _, created = UserSelfmadeBadge.objects.get_or_create(
        user=request.user,
        badge=badge,
    )
    if created:
        messages.success(request, f"Du har valt utmärkelsen {badge.name}.")
    else:
        messages.info(request, f"Du har redan valt utmärkelsen {badge.name}.")
    return redirect("selfmade_badges")


@login_required
@require_POST
def remove_selfmade_badge(request, badge_id):
    badge = get_object_or_404(SelfmadeBadge, pk=badge_id)
    deleted, _ = UserSelfmadeBadge.objects.filter(
        user=request.user,
        badge=badge,
    ).delete()
    if deleted:
        messages.success(request, f"Du har tagit bort utmärkelsen {badge.name}.")
    else:
        messages.info(request, f"Du hade inte valt utmärkelsen {badge.name}.")
    return redirect("selfmade_badges")
