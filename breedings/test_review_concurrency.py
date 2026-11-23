from concurrent.futures import ThreadPoolExecutor
from threading import Event

from django.contrib.auth import get_user_model
from django.db import connection, connections, transaction
from django.test import Client, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from associations.models import Association
from taxonomy.models import Genus, Species

from .models import BreedingRegistration


class ReviewConcurrencyTests(TransactionTestCase):
    def test_reviewer_waits_for_locked_report_and_keeps_first_decision(self):
        self.assertTrue(connection.mysql_is_mariadb)
        user_model = get_user_model()
        owner = user_model.objects.create_user(email="owner@example.com")
        approver = user_model.objects.create_superuser(email="approver@example.com")
        rejecter = user_model.objects.create_superuser(email="rejecter@example.com")
        species = Species.objects.create(
            genus=Genus.objects.create(scientific_name="Corydoras"),
            scientific_name="panda",
            breeding_class=Species.BreedingClass.SILVER,
        )
        report = BreedingRegistration.objects.create(
            owner=owner,
            association=Association.objects.create(name="Testförening"),
            species=species,
            breeding_date=timezone.localdate(),
            status=BreedingRegistration.Status.SUBMITTED,
        )
        url = reverse("breeding_review", args=[report.pk])
        self.client.force_login(approver)
        rejecting_client = Client()
        rejecting_client.force_login(rejecter)

        attempted_lock = Event()

        def observe_lock(execute, sql, params, many, context):
            if "FOR UPDATE" in sql.upper():
                attempted_lock.set()
            return execute(sql, params, many, context)

        def reject():
            try:
                with connection.execute_wrapper(observe_lock):
                    return rejecting_client.post(
                        url, {"reject": "1", "review_comment": "Andra beslutet"}
                    )
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=1) as executor:
            with transaction.atomic():
                BreedingRegistration.objects.select_for_update().get(pk=report.pk)
                pending = executor.submit(reject)
                self.assertTrue(
                    attempted_lock.wait(timeout=5), "POST låste inte rapporten"
                )
                self.assertFalse(pending.done())
                response = self.client.post(
                    url, {"approve": "1", "review_comment": "Första beslutet"}
                )
                self.assertEqual(response.status_code, 302)
            response = pending.result(timeout=10)

        self.assertRedirects(
            response, reverse("breeding_review_list"), fetch_redirect_response=False
        )
        report.refresh_from_db()
        self.assertEqual(report.status, BreedingRegistration.Status.APPROVED)
        self.assertEqual(report.reviewer_id, approver.pk)
        self.assertEqual(report.review_comment, "Första beslutet")
