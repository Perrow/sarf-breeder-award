from django.core.management.base import BaseCommand, CommandError

from taxonomy.species_import import SpeciesImportError, import_species_file


class Command(BaseCommand):
    help = "Importera arter och synonymer från en JSON-fil."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Sökväg till JSON-filen som ska importeras.")

    def handle(self, *args, **options):
        try:
            stats = import_species_file(options["path"])
        except SpeciesImportError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                "Import klar: "
                f"genera skapade {stats['genera_created']}, återanvända {stats['genera_reused']}; "
                f"arter skapade {stats['species_created']}, återanvända {stats['species_reused']}; "
                f"synonymer skapade {stats['synonyms_created']}, återanvända {stats['synonyms_reused']}."
            )
        )
