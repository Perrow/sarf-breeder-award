from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import AchievementRequirement, RequirementTextTemplate


class RequirementTextTemplateTests(TestCase):
    def test_default_templates_exist_for_all_requirement_kinds(self):
        self.assertEqual(
            set(RequirementTextTemplate.objects.values_list("kind", flat=True)),
            {
                AchievementRequirement.Kind.POINTS,
                AchievementRequirement.Kind.BREEDING_COUNT,
                AchievementRequirement.Kind.SPECIES_COUNT,
            },
        )

    def test_unknown_placeholder_is_rejected(self):
        template = RequirementTextTemplate.objects.get(
            kind=AchievementRequirement.Kind.SPECIES_COUNT
        )
        template.achieved_template = "Odla {unknown}."

        with self.assertRaises(ValidationError) as error:
            template.save()

        self.assertIn("Okända placeholders: unknown", str(error.exception))

    def test_malformed_template_is_rejected(self):
        template = RequirementTextTemplate.objects.get(
            kind=AchievementRequirement.Kind.SPECIES_COUNT
        )
        template.next_level_template = "Odla {missing_text"

        with self.assertRaises(ValidationError):
            template.save()


class RequirementTextTemplateAdminTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.superuser = User.objects.create_superuser(
            username="template-admin@example.com",
            email="template-admin@example.com",
            password="test-password",
        )
        self.staff_user = User.objects.create_user(
            username="template-staff@example.com",
            email="template-staff@example.com",
            password="test-password",
            is_staff=True,
        )
        self.url = reverse("admin:progression_requirementtexttemplate_changelist")

    def test_superuser_can_open_requirement_text_configuration(self):
        self.client.force_login(self.superuser)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kravtexter")
        self.assertContains(response, "Antal arter")
        self.assertContains(response, "Antal odlingar")
        self.assertContains(response, "Poäng")

    def test_non_superuser_cannot_open_requirement_text_configuration(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)
