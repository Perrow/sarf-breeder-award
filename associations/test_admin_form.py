from django import forms
from django.contrib import admin
from django.test import SimpleTestCase, TestCase

from .models import Association


class AssociationAdminFormTests(SimpleTestCase):
    def setUp(self):
        self.model_admin = admin.site._registry[Association]

    def test_admin_form_only_contains_requested_fields(self):
        fields = tuple(
            field
            for _title, options in self.model_admin.fieldsets
            for field in options["fields"]
        )

        self.assertEqual(
            fields,
            ("name", "description", "website_url", "email", "contact_person", "note"),
        )
        self.assertNotIn("organization_number", fields)
        self.assertNotIn("phone", fields)
        self.assertNotIn("address", fields)
        self.assertNotIn("postal_code", fields)
        self.assertNotIn("city", fields)

    def test_admin_list_uses_current_association_fields(self):
        self.assertEqual(
            self.model_admin.list_display,
            ("name", "email", "contact_person", "website_url"),
        )

    def test_admin_list_is_sorted_by_name_by_default(self):
        self.assertEqual(self.model_admin.ordering, ("name",))

    def test_description_uses_textarea(self):
        form_class = self.model_admin.get_form(request=None)
        form = form_class()

        self.assertIsInstance(form.fields["description"].widget, forms.Textarea)
        self.assertEqual(form.fields["description"].widget.attrs["rows"], 5)

    def test_note_and_contact_person_have_swedish_labels(self):
        self.assertEqual(
            Association._meta.get_field("contact_person").verbose_name,
            "kontaktperson",
        )
        self.assertEqual(Association._meta.get_field("note").verbose_name, "anteckning")
        self.assertEqual(
            Association._meta.get_field("description").verbose_name,
            "beskrivning",
        )


class AssociationContactDetailsTests(TestCase):
    def test_contact_person_and_note_can_be_saved(self):
        association = Association.objects.create(
            name="Testföreningen",
            email="kontakt@example.se",
            contact_person="Anna Andersson",
            website_url="https://example.se/",
            note="Intern anteckning om föreningen.",
        )

        saved = Association.objects.get(pk=association.pk)

        self.assertEqual(saved.contact_person, "Anna Andersson")
        self.assertEqual(saved.note, "Intern anteckning om föreningen.")
