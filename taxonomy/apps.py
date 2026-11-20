from django.apps import AppConfig


class TaxonomyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "taxonomy"
    verbose_name = "Taxonomi"

    def ready(self):
        from . import species_group_membership  # noqa: F401
