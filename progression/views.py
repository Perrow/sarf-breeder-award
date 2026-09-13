from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import AchievementBackground, DeMeritBadge, UserDeMeritBadge


@login_required
def demerit_badges(request):
    badges = DeMeritBadge.objects.filter(active=True).order_by("name")
    awarded_badge_ids = set(
        UserDeMeritBadge.objects.filter(user=request.user).values_list("badge_id", flat=True)
    )
    award_background = AchievementBackground.lifetime()
    return render(
        request,
        "progression/demerit_badges.html",
        {
            "badges": badges,
            "awarded_badge_ids": awarded_badge_ids,
            "award_background": award_background,
        },
    )


@login_required
@require_POST
def award_demerit_badge(request, badge_id):
    badge = get_object_or_404(DeMeritBadge, pk=badge_id, active=True)
    _, created = UserDeMeritBadge.objects.get_or_create(
        user=request.user,
        badge=badge,
    )
    if created:
        messages.success(request, f"Du har tilldelat dig märket {badge.name}.")
    else:
        messages.info(request, f"Du har redan märket {badge.name}.")
    return redirect("demerit_badges")
