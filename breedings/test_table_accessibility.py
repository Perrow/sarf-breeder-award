from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class TableAccessibilityMarkupTests(SimpleTestCase):
    def _template(self, relative_path):
        return (Path(settings.BASE_DIR) / relative_path).read_text(encoding="utf-8")

    def test_my_page_table_has_caption_column_headers_and_row_header(self):
        markup = self._template("breedings/templates/breedings/breeding_list.html")

        self.assertIn('<caption class="visually-hidden">Mina odlingsregistreringar</caption>', markup)
        self.assertIn('<th scope="col">Art</th>', markup)
        self.assertIn('<th scope="row" class="fw-normal">', markup)
        self.assertIn('<span class="visually-hidden">Åtgärd</span>', markup)

    def test_combined_leaderboards_have_accessible_table_structure(self):
        markup = self._template("breedings/templates/breedings/leaderboards.html")

        self.assertIn('Föreningstopplista för {{ selected_year }}', markup)
        self.assertIn('Individuell topplista för {{ selected_year }}', markup)
        self.assertGreaterEqual(markup.count('scope="col"'), 5)
        self.assertGreaterEqual(markup.count('scope="row"'), 2)

    def test_species_information_tables_have_accessible_table_structure(self):
        markup = self._template("breedings/templates/breedings/species_information.html")

        self.assertIn('Mina omklassningsbegäranden för {{ species }}', markup)
        self.assertIn('Godkända odlingar för {{ species }}', markup)
        self.assertGreaterEqual(markup.count('scope="col"'), 9)
        self.assertGreaterEqual(markup.count('scope="row"'), 2)

    def test_association_tables_have_captions_and_row_headers(self):
        templates = (
            "breedings/templates/breedings/association_leaderboard.html",
            "breedings/templates/breedings/association_member_leaderboard.html",
            "breedings/templates/breedings/association_member_breeding_list.html",
        )

        for relative_path in templates:
            with self.subTest(template=relative_path):
                markup = self._template(relative_path)
                self.assertIn('<caption class="visually-hidden">', markup)
                self.assertIn('scope="col"', markup)
                self.assertIn('scope="row"', markup)

    def test_individual_leaderboard_has_caption_and_row_headers(self):
        markup = self._template("breedings/templates/breedings/individual_leaderboard.html")

        self.assertIn('Individuell topplista för {{ selected_year }}', markup)
        self.assertEqual(markup.count('scope="col"'), 2)
        self.assertIn('scope="row"', markup)
