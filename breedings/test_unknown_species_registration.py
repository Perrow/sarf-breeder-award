from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class UnknownSpeciesRegistrationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="unknown-species@example.com", password="test-password",
        )
        self.client.force_login(self.user)

    def test_species_selection_contains_free_text_result_rendering(self):
        response = self.client.get(reverse("species_select"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Om du inte hittar den odlade arten i våra listor, välj den här och registrera ändå.",
        )
        self.assertContains(response, 'encodeURIComponent(query)')
        self.assertContains(response, 'items.length === 0')

    def test_unknown_species_search_returns_no_matches(self):
        response = self.client.get(
            reverse("species_search_results"), {"q": "Unknownus fictivus"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [])

    def test_selecting_free_text_prefills_genus_and_species(self):
        response = self.client.get(
            reverse("breeding_create"), {"free_text": "Unknownus fictivus"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"]["proposed_genus_name"].value(), "Unknownus")
        self.assertEqual(response.context["form"]["proposed_species_name"].value(), "fictivus")

    def test_one_word_prefills_genus_only(self):
        response = self.client.get(
            reverse("breeding_create"), {"free_text": "Unknownus"}
        )
        self.assertEqual(response.context["form"]["proposed_genus_name"].value(), "Unknownus")
        self.assertFalse(response.context["form"]["proposed_species_name"].value())

    def test_free_text_registration_has_no_species_dropdown(self):
        response = self.client.get(
            reverse("breeding_create"), {"free_text": "Unknownus fictivus"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<select name="species"')
        self.assertNotContains(response, '<label for="id_species">')
        self.assertContains(response, 'type="hidden" name="species"')
        self.assertContains(response, 'name="proposed_genus_name"')
        self.assertContains(response, 'name="proposed_species_name"')

    def test_free_text_mode_survives_invalid_form_submission(self):
        response = self.client.post(
            reverse("breeding_create") + "?free_text=Unknownus%20fictivus",
            {"proposed_genus_name": "Unknownus", "proposed_species_name": "fictivus"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<select name="species"')
        self.assertContains(response, 'name="proposed_genus_name"')
        self.assertContains(response, 'name="proposed_species_name"')

    def test_standard_registration_still_shows_species_dropdown(self):
        response = self.client.get(reverse("breeding_create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<select name="species"')
        self.assertContains(response, '<label for="id_species">')
