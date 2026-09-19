from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from associations.models import Association
from taxonomy.models import Genus, Species

from .models import BreedingRegistration
from .review import BREEDING_REVIEWER_GROUP
from .templatetags.breeding_markdown import render_limited_markdown


class LimitedBreedingMarkdownTests(SimpleTestCase):
    def test_heading_uses_lower_semantic_level(self):
        rendered = str(render_limited_markdown("# Lek och yngel"))

        self.assertIn('<h3 class="h5 mt-3 mb-2">Lek och yngel</h3>', rendered)
        self.assertNotIn("<h1", rendered)

    def test_bold_and_italic_are_rendered(self):
        rendered = str(
            render_limited_markdown("Det här är **viktigt** och *kursivt*.")
        )

        self.assertIn("<strong>viktigt</strong>", rendered)
        self.assertIn("<em>kursivt</em>", rendered)

    def test_bullet_lines_are_rendered_as_list(self):
        rendered = str(
            render_limited_markdown("- Första punkten\n- Andra punkten")
        )

        self.assertIn("<ul", rendered)
        self.assertIn("<li>Första punkten</li>", rendered)
        self.assertIn("<li>Andra punkten</li>", rendered)

    def test_plain_line_breaks_remain_visible(self):
        rendered = str(render_limited_markdown("Första raden\nAndra raden"))

        self.assertIn("Första raden<br>Andra raden", rendered)

    def test_raw_html_is_escaped(self):
        rendered = str(
            render_limited_markdown(
                '<script>alert("x")</script><img src=x onerror=alert(1)>'
            )
        )

        self.assertNotIn("<script>", rendered)
        self.assertNotIn("<img", rendered)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertIn("&lt;img", rendered)

    def test_unsupported_markdown_is_not_activated(self):
        rendered = str(
            render_limited_markdown(
                "## Inte en tillåten rubrik\n[En länk](https://example.com)"
            )
        )

        self.assertNotIn("<h2", rendered)
        self.assertNotIn("<a ", rendered)
        self.assertIn("## Inte en tillåten rubrik", rendered)
        self.assertIn("[En länk](https://example.com)", rendered)


class BreedingMarkdownPresentationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(
            username="markdown-owner@example.com",
            email="markdown-owner@example.com",
            password="test-password",
        )
        self.reviewer = User.objects.create_user(
            username="markdown-reviewer@example.com",
            email="markdown-reviewer@example.com",
            password="test-password",
        )
        self.reviewer.groups.add(
            Group.objects.get(name=BREEDING_REVIEWER_GROUP)
        )
        association = Association.objects.create(name="Markdownföreningen")
        genus = Genus.objects.create(scientific_name="Markdownus")
        species = Species.objects.create(
            genus=genus,
            scientific_name="testus",
            common_name="Markdownart",
            breeding_class=Species.BreedingClass.SILVER,
        )
        self.registration = BreedingRegistration.objects.create(
            owner=self.owner,
            association=association,
            species=species,
            breeding_date=timezone.localdate(),
            description=(
                "# Odlingsförlopp\n"
                "**Ägg** på rutan och *frisimmande* yngel.\n"
                "- Första kullen\n"
                "- Andra kullen\n"
                "<script>alert('x')</script>"
            ),
            status=BreedingRegistration.Status.SUBMITTED,
            submitted_at=timezone.now(),
        )

    def _assert_formatted_description(self, response):
        content = response.content.decode()

        self.assertIn(
            '<h3 class="h5 mt-3 mb-2">Odlingsförlopp</h3>',
            content,
        )
        self.assertIn("<strong>Ägg</strong>", content)
        self.assertIn("<em>frisimmande</em>", content)
        self.assertIn("<li>Första kullen</li>", content)
        self.assertIn("<li>Andra kullen</li>", content)
        self.assertNotIn("<script>alert", content)
        self.assertIn("&lt;script&gt;alert", content)

    def test_owner_sees_formatted_description(self):
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse("breeding_detail", args=[self.registration.pk])
        )

        self.assertEqual(response.status_code, 200)
        self._assert_formatted_description(response)

    def test_reviewer_sees_same_formatted_description(self):
        self.client.force_login(self.reviewer)

        response = self.client.get(
            reverse("breeding_review", args=[self.registration.pk])
        )

        self.assertEqual(response.status_code, 200)
        self._assert_formatted_description(response)
