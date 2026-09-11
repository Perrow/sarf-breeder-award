from django.contrib import admin
from django.test import SimpleTestCase

from .admin import CommonNameSynonymInline, ScientificSynonymInline, SpeciesAdmin
from .models import Species, SpeciesSynonym


class SynonymAdminRegistrationTests(SimpleTestCase):
    def test_species_synonym_is_not_registered_as_separate_admin_model(self):
        self.assertFalse(admin.site.is_registered(SpeciesSynonym))

    def test_species_admin_keeps_separate_synonym_inlines(self):
        model_admin = admin.site._registry[Species]

        self.assertIsInstance(model_admin, SpeciesAdmin)
        self.assertIn(ScientificSynonymInline, model_admin.inlines)
        self.assertIn(CommonNameSynonymInline, model_admin.inlines)
