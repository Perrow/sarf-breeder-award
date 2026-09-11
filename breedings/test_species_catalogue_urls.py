from urllib.parse import unquote

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class SpeciesCatalogueUrlTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="catalogue-url@example.com",
            password="test-password",
        )
        self.client.force_login(self.user)

    def test_querystring_search_redirects_permanently_to_canonical_path(self):
        response = self.client.get(reverse("species_catalogue"), {"q": "corydoras"})

        self.assertEqual(response.status_code, 301)
        self.assertEqual(
            response["Location"],
            reverse("species_catalogue_search", args=["corydoras"]),
        )

    def test_canonical_search_path_supplies_query_to_page(self):
        response = self.client.get(
            reverse("species_catalogue_search", args=["corydoras"])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["query"], "corydoras")
        self.assertContains(response, 'value="corydoras"')

    def test_search_url_encodes_spaces_and_swedish_characters(self):
        query = "räkor blå"
        url = reverse("species_catalogue_search", args=[query])

        self.assertNotIn(" ", url)
        self.assertEqual(unquote(url), f"/arter/listor/{query}/")

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["query"], query)

    def test_search_form_targets_canonical_path_with_javascript_and_has_get_fallback(self):
        response = self.client.get(reverse("species_catalogue"))

        self.assertContains(response, 'method="get"')
        self.assertContains(response, f'action="{reverse("species_catalogue")}"')
        self.assertContains(response, 'data-search-url-template=')
        self.assertContains(response, "encodeURIComponent(query)")
