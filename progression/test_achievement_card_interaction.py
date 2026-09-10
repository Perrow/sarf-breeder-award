from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Achievement, AchievementLevel, UserAchievement


class AchievementCardInteractionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="popover@example.com",
            email="popover@example.com",
            password="test-password",
        )
        self.client.force_login(self.user)

    def _earn(self, description="Detaljerad beskrivning", year=None):
        achievement = Achievement.objects.create(
            name="Interaktiv",
            calendar_year_based=year is not None,
        )
        level = AchievementLevel.objects.create(
            achievement=achievement,
            name="Silver",
            description=description,
            order=1,
        )
        return UserAchievement.objects.create(
            user=self.user,
            level=level,
            achievement_name=achievement.name,
            level_name=level.name,
            level_description=description,
            calendar_year=year,
        )

    def test_my_page_card_uses_hover_and_focus_popover(self):
        self._earn()

        response = self.client.get(reverse("breeding_list"))

        self.assertContains(response, 'data-bs-toggle="popover"')
        self.assertContains(response, 'data-bs-trigger="hover focus"')
        self.assertContains(response, 'data-bs-placement="auto"')
        self.assertContains(response, 'aria-label="Interaktiv – visa detaljer"')
        self.assertContains(
            response,
            'data-bs-content="Grad: Silver · Detaljerad beskrivning"',
        )
        self.assertContains(response, "data-achievement-details")
        self.assertContains(response, "new bootstrap.Popover(element);")

    def test_history_page_reuses_interactive_card_and_includes_year(self):
        self._earn(year=2026)

        response = self.client.get(reverse("achievements"))

        self.assertContains(response, 'data-bs-toggle="popover"')
        self.assertContains(
            response,
            'data-bs-content="Grad: Silver · År: 2026 · Detaljerad beskrivning"',
        )

    def test_card_without_description_has_clean_popover_content(self):
        self._earn(description="")

        response = self.client.get(reverse("breeding_list"))

        self.assertContains(response, 'data-bs-content="Grad: Silver"')
        self.assertNotContains(response, 'data-bs-content="Grad: Silver ·"')
