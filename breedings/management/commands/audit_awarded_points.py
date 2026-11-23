from collections import Counter

from django.core.management.base import BaseCommand

from breedings.models import BreedingRegistration
from breedings.scoring import BREEDING_CLASS_POINTS


class Command(BaseCommand):
    help = "Kontrollerar om historiskt sparade poäng avviker från tilldelad klass."

    def handle(self, *args, **options):
        counts = Counter()
        reports = (
            BreedingRegistration.objects.filter(status=BreedingRegistration.Status.APPROVED)
            .order_by()
            .values_list("awarded_breeding_class", "awarded_points")
        )
        for awarded_class, stored_points in reports.iterator():
            counts["total"] += 1
            expected = BREEDING_CLASS_POINTS.get(awarded_class)
            if expected is None:
                counts["missing_class"] += 1
            elif stored_points is None:
                counts["missing_points"] += 1
            elif stored_points != expected:
                counts["different_points"] += 1

        self.stdout.write(f"Godkända rapporter: {counts['total']}")
        self.stdout.write(f"Saknar giltig tilldelad klass: {counts['missing_class']}")
        self.stdout.write(f"Saknar sparade poäng: {counts['missing_points']}")
        self.stdout.write(
            f"Sparade poäng avviker från tilldelad klass: {counts['different_points']}"
        )
