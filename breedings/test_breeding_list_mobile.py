from types import SimpleNamespace

from django.template.loader import render_to_string
from django.test import SimpleTestCase
from django.urls import reverse


class BreedingListMobileMarkupTests(SimpleTestCase):
    def _render_registration(self, status):
        registration = SimpleNamespace(
            pk=42,
            status=status,
            breeding_date="2026-09-12",
            species=None,
            proposed_genus_name="Corydoras",
            proposed_species_name="panda",
            proposed_common_name="",
            awarded_breeding_class="",
            review_comment="",
            get_status_display=lambda: "Utkast" if status == "draft" else "Godkänd",
        )
        return render_to_string(
            "breedings/breeding_list.html",
            {
                "registrations": [registration],
                "yearly_achievements": [],
                "career_achievements": [],
            },
        )

    def test_mobile_columns_are_hidden_and_draft_row_targets_edit(self):
        html = self._render_registration("draft")
        edit_url = reverse("breeding_edit", args=[42])

        self.assertIn('<th class="d-none d-sm-table-cell">Datum</th>', html)
        self.assertIn('<td class="d-none d-sm-table-cell">2026-09-12</td>', html)
        self.assertIn('class="text-nowrap d-none d-sm-table-cell"', html)
        self.assertIn(f'data-mobile-href="{edit_url}"', html)
        self.assertIn(f'href="{edit_url}">Redigera</a>', html)

    def test_non_draft_row_targets_detail_and_has_keyboard_activation(self):
        html = self._render_registration("approved")
        detail_url = reverse("breeding_detail", args=[42])

        self.assertIn(f'data-mobile-href="{detail_url}"', html)
        self.assertIn(f'href="{detail_url}">Visa</a>', html)
        self.assertIn("row.tabIndex = 0", html)
        self.assertIn("row.setAttribute('role', 'link')", html)
        self.assertIn("event.key !== 'Enter' && event.key !== ' '", html)
