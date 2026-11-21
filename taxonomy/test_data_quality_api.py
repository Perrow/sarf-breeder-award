from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.test import TestCase
from django.urls import reverse

from .models import Geography, Genus, ScientificSpeciesSynonym, Species, SpeciesLink, SpeciesQualityReview


class RandomSpeciesDataQualityApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.genus = Genus.objects.create(scientific_name="Corydoras")

    def create_species(self, name, common=None, english=""):
        return Species.objects.create(
            genus=self.genus,
            scientific_name=name,
            common_name=common or f"Corydoras {name}",
            english_name=english,
            breeding_class=Species.BreedingClass.BRONZE,
        )

    def test_anonymous_request_returns_exactly_ten_eligible_species(self):
        for index in range(13):
            self.create_species(f"species{index}")
        complete = self.create_species("complete", common="Komplett", english="English")
        complete.geographies.add(Geography.objects.create(name="Sydamerika"))
        SpeciesLink.objects.create(
            species=complete, url="https://example.org/complete", source_name="Exempel"
        )

        response = self.client.get(reverse("species_data_quality_random"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 10)
        self.assertEqual(len({entry["id"] for entry in data["species"]}), 10)
        self.assertNotIn(complete.pk, {entry["id"] for entry in data["species"]})
        self.assertTrue(all(entry["quality_score"] >= 1 for entry in data["species"]))
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_missing_flags_match_admin_scoring_and_existing_metadata(self):
        species = self.create_species("aeneus")
        ScientificSpeciesSynonym.objects.create(
            species=species, scientific_name="Hoplisoma aeneum"
        )
        response = self.client.get(reverse("species_data_quality_random"))
        entry = response.json()["species"][0]
        self.assertEqual(entry["id"], species.pk)
        self.assertEqual(entry["full_scientific_name"], "Corydoras aeneus")
        self.assertEqual(entry["quality_score"], 4)
        self.assertEqual(entry["missing"], {
            "swedish_name": True,
            "english_name": True,
            "geography": True,
            "links": True,
        })
        self.assertEqual(entry["scientific_synonyms"], ["Hoplisoma aeneum"])
        self.assertEqual(entry["cl_number"], "")

        species.common_name = "Metallpansarmal"
        species.english_name = "Bronze cory"
        species.save(update_fields=["common_name", "english_name"])
        geography = Geography.objects.create(name="Amazonas")
        species.geographies.add(geography)
        response = self.client.get(reverse("species_data_quality_random"))
        entry = response.json()["species"][0]
        self.assertEqual(entry["quality_score"], 1)
        self.assertEqual(entry["missing"], {
            "swedish_name": False,
            "english_name": False,
            "geography": False,
            "links": True,
        })
        self.assertEqual(entry["geographies"], ["Amazonas"])

    def test_empty_result_and_fewer_than_ten_species(self):
        response = self.client.get(reverse("species_data_quality_random"))
        self.assertEqual(
            response.json(),
            {"count": 0, "page": 1, "next_page": None, "species": []},
        )
        species = self.create_species("panda")
        response = self.client.get(reverse("species_data_quality_random"))
        self.assertEqual(response.json()["species"][0]["id"], species.pk)
        self.assertEqual(response.json()["count"], 1)

    def test_only_get_is_allowed(self):
        url = reverse("species_data_quality_random")
        self.assertEqual(self.client.post(url, {}).status_code, 405)
        self.assertEqual(self.client.put(url, data="{}", content_type="application/json").status_code, 405)

    def test_api_does_not_require_login_or_leak_user_details(self):
        self.create_species("panda")
        user = get_user_model().objects.create_user(
            email="private@example.org", password="test-password"
        )
        response = self.client.get(reverse("species_data_quality_random"))
        self.assertNotIn(user.email, response.content.decode("utf-8"))

    def test_selection_is_deterministic_paged_and_prioritizes_highest_score(self):
        for index in range(12):
            self.create_species(f"species{index:02d}")
        lower = self.create_species("z_lower", common="Svenskt namn", english="English")
        response = self.client.get(reverse("species_data_quality_random"))
        first = response.json()
        self.assertEqual(first["page"], 1)
        self.assertEqual(first["next_page"], 2)
        self.assertEqual(len(first["species"]), 10)
        self.assertTrue(all(row["quality_score"] == 4 for row in first["species"]))
        self.assertEqual(
            [row["scientific_name"] for row in first["species"]],
            [f"species{index:02d}" for index in range(10)],
        )
        second = self.client.get(reverse("species_data_quality_random"), {"page": "2"}).json()
        self.assertEqual(second["next_page"], None)
        self.assertEqual(len(second["species"]), 3)
        self.assertEqual(second["species"][-1]["id"], lower.pk)
        self.assertEqual(
            {row["id"] for row in first["species"]}.intersection(
                {row["id"] for row in second["species"]}
            ),
            set(),
        )

    def test_reviewed_species_are_excluded_until_due_and_manual_review_is_excluded(self):
        reviewed = self.create_species("reviewed")
        manual = self.create_species("manual")
        waiting = self.create_species("waiting")
        today = timezone.localdate()
        SpeciesQualityReview.objects.create(
            species=reviewed, status=SpeciesQualityReview.Status.REVIEWED,
            reviewed_at=today - timedelta(days=30),
            review_again_after=today + timedelta(days=335),
        )
        SpeciesQualityReview.objects.create(
            species=manual, status=SpeciesQualityReview.Status.MANUAL_REVIEW,
            reviewed_at=today, review_again_after=None,
        )
        response = self.client.get(reverse("species_data_quality_random"))
        self.assertEqual([row["id"] for row in response.json()["species"]], [waiting.pk])
        obj = SpeciesQualityReview.objects.get(species=reviewed)
        obj.review_again_after = today
        obj.save(update_fields=["review_again_after"])
        response = self.client.get(reverse("species_data_quality_random"))
        self.assertEqual({row["id"] for row in response.json()["species"]}, {reviewed.pk, waiting.pk})
        reviewed_row = next(row for row in response.json()["species"] if row["id"] == reviewed.pk)
        self.assertEqual(reviewed_row["review"]["status"], "reviewed")

    def test_invalid_page_is_rejected(self):
        for value in ("0", "-1", "invalid", "100001"):
            with self.subTest(value=value):
                self.assertEqual(
                    self.client.get(reverse("species_data_quality_random"), {"page": value}).status_code,
                    400,
                )
