from django.urls import path

from .views import award_selfmade_badge, selfmade_badges

urlpatterns = [
    path("utmarkelser/selfmade/", selfmade_badges, name="selfmade_badges"),
    path(
        "utmarkelser/selfmade/<int:badge_id>/tilldela/",
        award_selfmade_badge,
        name="award_selfmade_badge",
    ),
]
