from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse


class FormLayoutTests(TestCase):
    def test_shared_form_stylesheet_is_discoverable(self):
        self.assertIsNotNone(finders.find("css/forms.css"))

    def test_login_uses_shared_form_layout_and_stylesheet(self):
        response = self.client.get(reverse("login"))

        self.assertContains(response, 'class="site-form"')
        self.assertContains(response, 'href="/static/css/forms.css"')

    def test_registration_uses_shared_form_layout(self):
        response = self.client.get(reverse("register"))

        self.assertContains(response, 'class="site-form"')
        self.assertContains(response, 'class="col-12 col-md-8 col-lg-6 form-page"')

    def test_password_reset_uses_shared_form_layout(self):
        response = self.client.get(reverse("password_reset"))

        self.assertContains(response, 'class="site-form"')
        self.assertContains(response, 'class="form-intro"')
