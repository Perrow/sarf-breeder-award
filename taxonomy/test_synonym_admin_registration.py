from django.contrib import admin
from django.test import SimpleTestCase

from .models import CommonNameSpeciesSynonym, ScientificSpeciesSynonym


class SynonymAdminRegistrationTests(SimpleTestCase):
    def test_synonym_models_are_not_registered_as_separate_admin_models(self):
        self.assertFalse(admin.site.is_registered(ScientificSpeciesSynonym))
        self.assertFalse(admin.site.is_registered(CommonNameSpeciesSynonym))

