from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from .models import Association


class DjangoPermissionAdminTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="permission-admin@example.com",
            email="permission-admin@example.com",
            password="test-password",
            is_staff=True,
        )
        self.association = Association.objects.create(name="Behörighetsföreningen")
        self.client.force_login(self.user)

    def test_staff_user_without_permission_cannot_open_association_admin(self):
        response = self.client.get(reverse("admin:associations_association_changelist"))
        self.assertEqual(response.status_code, 403)

    def test_view_permission_gives_read_access_to_association_admin(self):
        self.user.user_permissions.add(
            Permission.objects.get(codename="view_association")
        )

        response = self.client.get(reverse("admin:associations_association_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.association.name)

    def test_change_permission_allows_editing_association(self):
        self.user.user_permissions.add(
            Permission.objects.get(codename="view_association"),
            Permission.objects.get(codename="change_association"),
        )

        response = self.client.post(
            reverse("admin:associations_association_change", args=[self.association.pk]),
            {
                "name": "Ändrad förening",
                "organization_number": "",
                "email": "",
                "phone": "",
                "address": "",
                "postal_code": "",
                "city": "",
                "description": "",
                "_save": "Spara",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.association.refresh_from_db()
        self.assertEqual(self.association.name, "Ändrad förening")
