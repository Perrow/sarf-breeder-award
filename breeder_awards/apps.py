from django.apps import AppConfig


class BreederAwardsConfig(AppConfig):
    name = "breeder_awards"

    def ready(self):
        from django.contrib import admin

        from .db_collations import register_sqlite_collations

        register_sqlite_collations()
        admin.site.site_header = "Odlingskampanjen – administration"
        admin.site.site_title = "Odlingskampanjen – administration"
        admin.site.index_title = "Administration"
