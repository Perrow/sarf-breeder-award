from types import SimpleNamespace

from django.template.loader import render_to_string
from django.test import TestCase

from progression.forms import (
    AchievementAdminForm,
    ManualAwardAdminForm,
    SelfmadeBadgeAdminForm,
)
from progression.models import Achievement, ManualAward, SelfmadeBadge


class SharedAwardImageTests(TestCase):
    def setUp(self):
        self.achievement = Achievement.objects.create(name="Delad bildkälla")
        Achievement.objects.filter(pk=self.achievement.pk).update(
            image="achievements/images/shared-overlay.png",
            background_image="achievements/custom_backgrounds/shared-background.png",
        )
        self.achievement.refresh_from_db()

        self.manual_award = ManualAward.objects.create(name="Manuell bildkälla")
        ManualAward.objects.filter(pk=self.manual_award.pk).update(
            image="achievements/manual/manual-overlay.png",
            background_image="achievements/custom_backgrounds/manual-background.png",
        )
        self.manual_award.refresh_from_db()

        self.selfmade_badge = SelfmadeBadge.objects.create(name="Egenvald bildkälla")
        SelfmadeBadge.objects.filter(pk=self.selfmade_badge.pk).update(
            image="achievements/selfmade/selfmade-overlay.png",
            background_image="achievements/custom_backgrounds/selfmade-background.png",
        )
        self.selfmade_badge.refresh_from_db()

    def _assert_all_images_are_reusable(self, form):
        overlay_values = {value for value, _label in form.fields["existing_image"].choices}
        background_values = {
            value for value, _label in form.fields["existing_background_image"].choices
        }

        self.assertIn(self.achievement.image.name, overlay_values)
        self.assertIn(self.manual_award.image.name, overlay_values)
        self.assertIn(self.selfmade_badge.image.name, overlay_values)
        self.assertIn(self.achievement.background_image.name, background_values)
        self.assertIn(self.manual_award.background_image.name, background_values)
        self.assertIn(self.selfmade_badge.background_image.name, background_values)

    def test_achievement_can_reuse_images_from_all_award_types(self):
        self._assert_all_images_are_reusable(AchievementAdminForm())

    def test_manual_award_can_reuse_images_from_all_award_types(self):
        self._assert_all_images_are_reusable(ManualAwardAdminForm())

    def test_selfmade_award_can_reuse_images_from_all_award_types(self):
        self._assert_all_images_are_reusable(SelfmadeBadgeAdminForm())

    def test_manual_award_card_prefers_custom_background(self):
        grant = SimpleNamespace(pk=1, award=self.manual_award, awarded_on="2026-09-13")

        html = render_to_string(
            "progression/includes/manual_award_card.html",
            {"grant": grant, "award_background": None},
        )

        self.assertIn("manual-background.png", html)

    def test_selfmade_award_card_prefers_custom_background(self):
        grant = SimpleNamespace(pk=1, badge=self.selfmade_badge, awarded_at="2026-09-13")

        html = render_to_string(
            "progression/includes/selfmade_badge_card.html",
            {"grant": grant, "award_background": None},
        )

        self.assertIn("selfmade-background.png", html)
