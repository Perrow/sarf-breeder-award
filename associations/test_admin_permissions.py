from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .admin import (
    ASSOCIATION_ADMIN_GROUP,
    MEMBER_GROUP,
    SYSTEM_ADMIN_GROUP,
    AssociationAdmin,
    MembershipAdmin,
)
from .models import Association, Membership


class AssociationAdministrationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.system_admin = User.objects.create_user(
            username="system@example.com",
            email="system@example.com",
            password="test-password",
            is_staff=True,
        )
        self.association_admin = User.objects.create_user(
            username="association@example.com",
            email="association@example.com",
            password="test-password",
            is_staff=True,
            first_name="Anna",
            last_name="Admin",
        )
        self.member = User.objects.create_user(
            username="member@example.com",
            email="member@example.com",
            password="test-password",
            is_staff=True,
        )
        self.new_member = User.objects.create_user(
            username="new@example.com",
            email="new@example.com",
            password="test-password",
            first_name="Ny",
            last_name="Medlem",
        )

        self.system_group = Group.objects.get(name=SYSTEM_ADMIN_GROUP)
        self.association_group = Group.objects.get(name=ASSOCIATION_ADMIN_GROUP)
        self.member_group = Group.objects.get(name=MEMBER_GROUP)
        self.system_admin.groups.add(self.system_group)
        self.association_admin.groups.add(self.association_group)
        self.member.groups.add(self.member_group)

        self.own_association = Association.objects.create(name="Egen förening")
        self.other_association = Association.objects.create(name="Annan förening")
        Membership.objects.create(
            user=self.association_admin,
            association=self.own_association,
            member_number="ADMIN-1",
        )
        Membership.objects.create(
            user=self.member,
            association=self.other_association,
            member_number="200",
        )

        self.factory = RequestFactory()

    def _request_for(self, user):
        request = self.factory.get("/admin/")
        request.user = user
        return request

    def test_role_groups_are_created(self):
        self.assertTrue(Group.objects.filter(name=SYSTEM_ADMIN_GROUP).exists())
        self.assertTrue(Group.objects.filter(name=ASSOCIATION_ADMIN_GROUP).exists())
        self.assertTrue(Group.objects.filter(name=MEMBER_GROUP).exists())

    def test_system_admin_can_see_all_associations(self):
        model_admin = admin.site._registry[Association]
        self.assertIsInstance(model_admin, AssociationAdmin)

        queryset = model_admin.get_queryset(self._request_for(self.system_admin))

        self.assertSetEqual(
            set(queryset.values_list("pk", flat=True)),
            {self.own_association.pk, self.other_association.pk},
        )

    def test_association_admin_only_sees_own_association(self):
        model_admin = admin.site._registry[Association]

        queryset = model_admin.get_queryset(self._request_for(self.association_admin))

        self.assertSetEqual(
            set(queryset.values_list("pk", flat=True)),
            {self.own_association.pk},
        )

    def test_association_admin_is_denied_other_association(self):
        self.client.force_login(self.association_admin)

        response = self.client.get(
            reverse("admin:associations_association_change", args=[self.other_association.pk])
        )

        self.assertEqual(response.status_code, 403)

    def test_association_admin_can_add_membership_to_own_association(self):
        self.client.force_login(self.association_admin)

        response = self.client.post(
            reverse("admin:associations_membership_add"),
            {
                "user": self.new_member.pk,
                "association": self.own_association.pk,
                "member_number": "300",
                "phone": "070-1234567",
                "association_data": "",
                "_save": "Spara",
            },
        )

        self.assertEqual(response.status_code, 302)
        membership = Membership.objects.get(
            user=self.new_member,
            association=self.own_association,
        )
        self.assertEqual(membership.member_number, "300")
        self.assertEqual(membership.phone, "070-1234567")

    def test_association_admin_cannot_add_membership_to_other_association(self):
        self.client.force_login(self.association_admin)

        response = self.client.post(
            reverse("admin:associations_membership_add"),
            {
                "user": self.new_member.pk,
                "association": self.other_association.pk,
                "member_number": "301",
                "phone": "070-7654321",
                "association_data": "",
                "_save": "Spara",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Membership.objects.filter(
                user=self.new_member,
                association=self.other_association,
            ).exists()
        )

    def test_member_has_no_association_admin_access(self):
        association_admin = admin.site._registry[Association]
        membership_admin = admin.site._registry[Membership]
        request = self._request_for(self.member)

        self.assertFalse(association_admin.has_module_permission(request))
        self.assertFalse(membership_admin.has_module_permission(request))

    def test_membership_admin_exposes_member_registry_fields(self):
        model_admin = admin.site._registry[Membership]
        self.assertIsInstance(model_admin, MembershipAdmin)
        self.assertEqual(
            model_admin.list_display,
            ("user_name", "user_email", "phone", "member_number", "association"),
        )
