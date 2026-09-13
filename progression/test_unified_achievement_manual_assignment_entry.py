from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from progression.models import Achievement


class UnifiedAchievementManualAssignmentEntryTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="manual-entry-admin",
            email="manual-entry-admin@example.com",
            password="Test-password-123",
        )
        self.client.force_login(self.admin)

    def test_unified_achievement_list_exposes_manual_assignment_entry(self):
        Achievement.objects.create(
            name="Manuell utmärkelse",
            achievement_type=Achievement.Type.MANUAL,
        )

        response = self.client.get(reverse("admin:progression_achievement_changelist"))

        self.assertContains(response, "Tilldela manuella utmärkelser")
        self.assertContains(response, "achievement_type__exact=manual")

    def test_manual_filter_keeps_assignment_inside_unified_achievement_admin(self):
        Achievement.objects.create(
            name="Manuell utmärkelse",
            achievement_type=Achievement.Type.MANUAL,
        )
        Achievement.objects.create(
            name="Karriärutmärkelse",
            achievement_type=Achievement.Type.CAREER,
        )

        response = self.client.get(
            reverse("admin:progression_achievement_changelist"),
            {"achievement_type__exact": Achievement.Type.MANUAL},
        )

        self.assertContains(response, "Manuell utmärkelse")
        self.assertNotContains(response, "Karriärutmärkelse")
