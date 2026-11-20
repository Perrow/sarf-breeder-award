from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Geography, Genus, Species, SpeciesDataQuality, SpeciesLink


class SpeciesDataQualityAdminTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            email="data-quality-admin@example.com", password="test-password"
        )
        self.client.force_login(self.admin_user)
        self.genus = Genus.objects.create(scientific_name="Apistogramma")
        self.url = reverse("admin:taxonomy_speciesdataquality_changelist")

    def add_species(self, epithet, common_name=None, english_name=""):
        return Species.objects.create(
            genus=self.genus,
            scientific_name=epithet,
            common_name=common_name or f"Apistogramma {epithet}",
            english_name=english_name,
            breeding_class=Species.BreedingClass.SILVER,
        )

    def results(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        return response, list(response.context["cl"].result_list)

    def test_four_criteria_and_descending_score(self):
        complete = self.add_species("complete", "Komplett", "English name")
        missing_one = self.add_species("one", english_name="English name")
        missing_two = self.add_species("two", "Svenskt namn", "")
        missing_three = self.add_species("three", "Svenskt namn", "")
        missing_four = self.add_species("four")

        geography = Geography.objects.create(name="Sydamerika")
        for species in (complete, missing_one, missing_two, missing_four):
            species.geographies.add(geography)
        # A duplicate geography/link must not inflate or duplicate the result.
        second_geography = Geography.objects.create(name="Amazonas")
        complete.geographies.add(second_geography)
        for species in (complete, missing_one, missing_three):
            SpeciesLink.objects.create(
                species=species, source_name="Källa",
                url=f"https://example.org/species/{species.pk}",
            )
        SpeciesLink.objects.create(
            species=complete, source_name="Annan källa",
            url="https://example.org/another",
        )
        # Remove geography from 'four' so it is missing all four criteria.
        missing_four.geographies.clear()

        response, rows = self.results()
        self.assertEqual(
            [(item.pk, item.quality_score) for item in rows],
            [
                (missing_four.pk, 4),
                (missing_three.pk, 2),
                (missing_two.pk, 2),
                (missing_one.pk, 1),
                (complete.pk, 0),
            ],
        )
        self.assertEqual(rows[0].swedish_name_gap, 1)
        self.assertEqual(rows[0].english_name_gap, 1)
        self.assertEqual(rows[0].geography_gap, 1)
        self.assertEqual(rows[0].link_gap, 1)
        model_admin = admin.site._registry[SpeciesDataQuality]
        for item in rows:
            self.assertEqual(model_admin.missing_swedish_name(item), item.swedish_name_gap == 0)
            self.assertEqual(model_admin.missing_english_name(item), item.english_name_gap == 0)
            self.assertEqual(model_admin.missing_geography(item), item.geography_gap == 0)
            self.assertEqual(model_admin.missing_link(item), item.link_gap == 0)
        self.assertContains(response, "Grön bock betyder att uppgiften finns")
        self.assertContains(response, "Maximalt 4 poäng")
        self.assertContains(response, reverse("admin:taxonomy_species_change", args=[missing_four.pk]))

    def test_ties_are_sorted_alphabetically_and_inactive_species_are_included(self):
        zulu = self.add_species("zulu")
        alpha = self.add_species("alpha")
        alpha.is_active = False
        alpha.save(update_fields=["is_active"])
        _, rows = self.results()
        self.assertEqual([row.pk for row in rows], [alpha.pk, zulu.pk])

    def test_admin_menu_contains_data_quality(self):
        response = self.client.get(reverse("admin:index"))
        self.assertContains(response, "Datakvalitet")
        self.assertContains(response, self.url)

    def test_list_is_read_only_but_links_to_original_species_editor(self):
        model_admin = admin.site._registry[SpeciesDataQuality]
        self.assertFalse(model_admin.has_add_permission(self._request()))
        self.assertFalse(model_admin.has_change_permission(self._request()))
        species = self.add_species("test")
        response, _ = self.results()
        self.assertContains(response, reverse("admin:taxonomy_species_change", args=[species.pk]))

    def _request(self):
        from django.test import RequestFactory
        request = RequestFactory().get(self.url)
        request.user = self.admin_user
        return request

    def test_user_without_species_permission_cannot_see_data_quality(self):
        user = get_user_model().objects.create_user(
            email="no-quality-permission@example.com",
            password="test-password",
            is_staff=True,
        )
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
