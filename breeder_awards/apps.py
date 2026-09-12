from django.apps import AppConfig


class BreederAwardsConfig(AppConfig):
    name = "breeder_awards"

    def ready(self):
        from .db_collations import register_sqlite_collations

        register_sqlite_collations()
