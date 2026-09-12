from pathlib import Path

from django import forms
from django.conf import settings
from django.template import Context, Template
from django.template.loader import render_to_string
from django.test import SimpleTestCase


class AccessibleTestForm(forms.Form):
    name = forms.CharField(label="Namn", help_text="Ange ditt namn.")


class FormAccessibilityTests(SimpleTestCase):
    def test_error_summary_links_to_invalid_field(self):
        form = AccessibleTestForm(data={})
        self.assertFalse(form.is_valid())

        html = render_to_string("includes/form_error_summary.html", {"form": form})

        self.assertIn('role="alert"', html)
        self.assertIn('aria-labelledby="form-error-summary-title"', html)
        self.assertIn('href="#id_name"', html)
        self.assertIn("Namn", html)

    def test_django_field_describes_help_text_and_validation_error(self):
        form = AccessibleTestForm(data={})
        self.assertFalse(form.is_valid())

        html = Template(
            '{{ form.name.errors }}{{ form.name }}'
            '<div id="{{ form.name.auto_id }}_helptext">{{ form.name.help_text }}</div>'
        ).render(Context({"form": form}))

        self.assertIn('id="id_name_error"', html)
        self.assertIn('id="id_name_helptext"', html)
        self.assertIn('aria-invalid="true"', html)
        self.assertIn('aria-describedby="id_name_helptext id_name_error"', html)

    def test_required_form_flows_include_error_summary(self):
        templates = (
            "users/templates/users/register.html",
            "users/templates/users/login.html",
            "users/templates/users/account_edit.html",
            "users/templates/users/password_reset_form.html",
            "users/templates/users/password_reset_confirm.html",
            "breedings/templates/breedings/breeding_form.html",
            "breedings/templates/breedings/species_reclassification_request.html",
        )

        for relative_path in templates:
            with self.subTest(template=relative_path):
                source = (Path(settings.BASE_DIR) / relative_path).read_text(encoding="utf-8")
                self.assertIn('{% include "includes/form_error_summary.html" %}', source)

    def test_manual_breeding_help_text_uses_django_describedby_ids(self):
        source = (
            Path(settings.BASE_DIR)
            / "breedings"
            / "templates"
            / "breedings"
            / "breeding_form.html"
        ).read_text(encoding="utf-8")

        self.assertIn('id="{{ form.breeding_date.auto_id }}_helptext"', source)
        self.assertIn('id="{{ form.description.auto_id }}_helptext"', source)
