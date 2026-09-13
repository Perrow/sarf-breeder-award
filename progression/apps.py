from django.apps import AppConfig


class ProgressionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "progression"
    verbose_name = "Utmärkelser"

    def ready(self):
        from . import manual_awards_admin  # noqa: F401
