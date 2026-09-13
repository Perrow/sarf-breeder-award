from django.urls import path

from .views import award_demerit_badge, demerit_badges

urlpatterns = [
    path("utmarkelser/demerit/", demerit_badges, name="demerit_badges"),
    path(
        "utmarkelser/demerit/<int:badge_id>/tilldela/",
        award_demerit_badge,
        name="award_demerit_badge",
    ),
]
