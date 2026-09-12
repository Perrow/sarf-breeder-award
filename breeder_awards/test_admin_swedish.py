from django.apps import apps
from django.contrib import admin
from django.test import SimpleTestCase

from associations.models import Association, Membership
from progression.admin import AchievementAdmin, AchievementBackgroundAdmin
from progression.models import (
    AchievementBackground,
    AchievementRequirement,
    RequirementTextTemplate,
    UserAchievement,
)
from taxonomy.models import Genus


class SwedishAdminTextTests(SimpleTestCase):
    def test_project_admin_sections_have_swedish_names(self):
        expected_names = {
            "users": "Användare",
            "associations": "Föreningar",
            "taxonomy": "Taxonomi",
            "breedings": "odlingar",
            "progression": "Utmärkelser",
            "siteconfig": "Sidinställningar",
        }

        for app_label, expected_name in expected_names.items():
            with self.subTest(app_label=app_label):
                self.assertEqual(apps.get_app_config(app_label).verbose_name, expected_name)

    def test_admin_site_headings_are_swedish(self):
        self.assertEqual(admin.site.site_header, "Odlingskampanjen – administration")
        self.assertEqual(admin.site.site_title, "Odlingskampanjen – administration")
        self.assertEqual(admin.site.index_title, "Administration")

    def test_association_admin_model_and_field_names_are_swedish(self):
        self.assertEqual(Association._meta.verbose_name, "förening")
        self.assertEqual(Association._meta.verbose_name_plural, "föreningar")
        self.assertEqual(Association._meta.get_field("organization_number").verbose_name, "organisationsnummer")
        self.assertEqual(Association._meta.get_field("email").verbose_name, "e-post")
        self.assertEqual(Membership._meta.verbose_name, "medlemskap")
        self.assertEqual(Membership._meta.get_field("member_number").verbose_name, "medlemsnummer")
        self.assertEqual(Membership._meta.get_field("association_data").verbose_name, "föreningsuppgifter")

    def test_taxonomy_admin_uses_swedish_genus_terms(self):
        self.assertEqual(Genus._meta.verbose_name, "släkte")
        self.assertEqual(Genus._meta.verbose_name_plural, "släkten")
        self.assertEqual(Genus._meta.get_field("scientific_name").verbose_name, "vetenskapligt namn")
        self.assertEqual(Genus._meta.get_field("is_active").verbose_name, "aktiv")

    def test_progression_admin_labels_do_not_use_english_admin_terms(self):
        self.assertEqual(AchievementRequirement._meta.get_field("genera").verbose_name, "släkten")
        self.assertEqual(UserAchievement._meta.get_field("achievement_name").verbose_name, "utmärkelse")
        self.assertEqual(UserAchievement._meta.get_field("level_description").verbose_name, "nivåbeskrivning")
        self.assertIn("platshållare", RequirementTextTemplate.PLACEHOLDER_HELP)
        self.assertNotIn("placeholders", RequirementTextTemplate.PLACEHOLDER_HELP)

        achievement_admin = AchievementAdmin(admin.site._registry[AchievementAdmin.model].model, admin.site)
        self.assertEqual(str(achievement_admin.preview(None)), "Spara utmärkelsen för att visa förhandsvisningen.")

        background_admin = AchievementBackgroundAdmin(AchievementBackground, admin.site)
        background = type("Background", (), {"calendar_year": None})()
        self.assertEqual(background_admin.background_type(background), "Livstid")

    def test_achievement_background_help_text_is_swedish(self):
        self.assertEqual(
            AchievementBackground._meta.get_field("calendar_year").help_text,
            "Lämna tomt för livstidsbakgrunden.",
        )
        self.assertNotIn(
            "lifetime",
            AchievementBackground._meta.get_field("calendar_year").help_text.lower(),
        )
