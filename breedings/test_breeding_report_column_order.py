from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class BreedingReportColumnOrderTests(SimpleTestCase):
    def _template(self, name):
        return (
            Path(settings.BASE_DIR)
            / "breedings"
            / "templates"
            / "breedings"
            / name
        ).read_text(encoding="utf-8")

    def test_my_page_lists_species_before_date(self):
        template = self._template("breeding_list.html")

        self.assertLess(template.index("<th>Art</th>"), template.index(">Datum</th>"))
        self.assertLess(
            template.index("{% if registration.species %}"),
            template.index("{{ registration.breeding_date }}"),
        )

    def test_association_member_list_lists_species_before_date(self):
        template = self._template("association_member_breeding_list.html")

        self.assertLess(template.index("<th>Art</th>"), template.index("<th>Odlingsdatum</th>"))
        self.assertLess(
            template.index("{{ row.registration.species }}"),
            template.index("{{ row.registration.breeding_date }}"),
        )
