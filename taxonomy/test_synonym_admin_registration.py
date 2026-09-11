from django.contrib import admin
from django.test import SimpleTestCase

from .admin import CommonNameSynonymInline, ScientificSynonymInline, SpeciesAdmin
from .models import CommonNameSpeciesSynonym, ScientificSpeciesSynonym, Species


class SynonymAdminRegistrationTests(SimpleTestCase):
    def test_synonym_models_are_not_registered_as_separate_admin_models(self):
        self.assertFalse(admin.site.is_registered(ScientificSpeciesSynonym))
        self.assertFalse(admin.site.is_registered(CommonNameSpeciesSynonym))

    def test_species_admin_keeps_separate_synonym_inlines(self):
        model_admin = admin.site._registry[Species]

        self.assertIsInstance(model_admin, SpeciesAdmin)
        self.assertIn(ScientificSynonymInline, model_admin.inlines)
        self.assertIn(CommonNameSynonymInline, model_admin.inlines)
