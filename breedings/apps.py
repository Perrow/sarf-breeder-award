from django.apps import AppConfig


class BreedingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "breedings"
    verbose_name = "odlingar"

    def ready(self):
        from . import reclassification_admin  # noqa: F401
