from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Achievement, AchievementLevel, UserAchievement


class AchievementCardInteractionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="modal@example.com",
            email="modal@example.com",
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

    def test_my_page_card_opens_accessible_modal_with_details(self):
        earned = self._earn()

        response = self.client.get(reverse("breeding_list"))

        self.assertContains(response, 'data-bs-toggle="modal"')
        self.assertContains(response, f'data-bs-target="#achievement-modal-{earned.pk}"')
        self.assertContains(response, 'aria-label="Interaktiv – visa detaljer"')
        self.assertContains(response, 'aria-label="Stäng"')
        self.assertContains(response, "<strong>Nivå:</strong> Silver", html=True)
        self.assertContains(response, "Detaljerad beskrivning")
        self.assertNotContains(response, 'data-bs-toggle="popover"')

    def test_history_page_modal_includes_year(self):
        self._earn(year=2026)

        response = self.client.get(reverse("achievements"))

        self.assertContains(response, 'data-bs-toggle="modal"')
        self.assertContains(response, "<strong>År:</strong> 2026", html=True)

    def test_card_without_description_has_clean_modal_content(self):
        self._earn(description="")

        response = self.client.get(reverse("breeding_list"))

        self.assertContains(response, "<strong>Nivå:</strong> Silver", html=True)
        self.assertNotContains(response, "Detaljerad beskrivning")
