from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .admin import ASSOCIATION_ADMIN_GROUP, MEMBER_GROUP, SYSTEM_ADMIN_GROUP
from .models import Association, Membership


class AssociationAdministrationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.system_admin = User.objects.create_user(
            username="system-admin@example.com",
            email="system-admin@example.com",
            password="test-password",
            is_staff=True,
        )
        self.association_admin = User.objects.create_user(
            username="association-admin@example.com",
            email="association-admin@example.com",
            password="test-password",
            is_staff=True,
        )
        self.member = User.objects.create_user(
            username="member@example.com",
            email="member@example.com",
            password="test-password",
            is_staff=True,
        )
        self.own_association = Association.objects.create(name="Egen förening")
        self.other_association = Association.objects.create(name="Annan förening")

        self.system_admin.groups.add(Group.objects.get(name=SYSTEM_ADMIN_GROUP))
        self.association_admin.groups.add(Group.objects.get(name=ASSOCIATION_ADMIN_GROUP))
        self.member.groups.add(Group.objects.get(name=MEMBER_GROUP))

        Membership.objects.create(
            user=self.association_admin,
            association=self.own_association,
            is_association_admin=True,
        )
        Membership.objects.create(
            user=self.member,
            association=self.own_association,
        )
        self.factory = RequestFactory()

    def _request_for(self, user):
        request = self.factory.get("/admin/")
        request.user = user
        return request

    def test_expected_groups_exist(self):
        self.assertTrue(Group.objects.filter(name=SYSTEM_ADMIN_GROUP).exists())
        self.assertTrue(Group.objects.filter(name=ASSOCIATION_ADMIN_GROUP).exists())
        self.assertTrue(Group.objects.filter(name=MEMBER_GROUP).exists())

    def test_member_has_no_association_admin_access(self):
        association_admin = admin.site._registry[Association]
        membership_admin = admin.site._registry[Membership]
        request = self._request_for(self.member)

        self.assertFalse(association_admin.has_module_permission(request))
        self.assertFalse(membership_admin.has_module_permission(request))

    def test_system_admin_sees_all_associations(self):
        model_admin = admin.site._registry[Association]

        queryset = model_admin.get_queryset(self._request_for(self.system_admin))

        self.assertSetEqual(
            set(queryset.values_list("pk", flat=True)),
            {self.own_association.pk, self.other_association.pk},
        )

    def test_association_admin_uses_dedicated_interface_not_django_admin(self):
        association_admin = admin.site._registry[Association]
        membership_admin = admin.site._registry[Membership]
        request = self._request_for(self.association_admin)

        self.assertFalse(association_admin.has_module_permission(request))
        self.assertFalse(membership_admin.has_module_permission(request))

        self.client.force_login(self.association_admin)
        response = self.client.get(reverse("admin:associations_association_changelist"))
        self.assertEqual(response.status_code, 403)
