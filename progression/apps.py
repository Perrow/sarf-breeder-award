from django.apps import AppConfig


class ProgressionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "progression"
    verbose_name = "Utmärkelser"

    def ready(self):
        from django.contrib import admin

        from . import admin as progression_admin
        from . import manual_assignment_admin  # noqa: F401

        base_get_app_list = progression_admin._default_get_app_list

        def get_app_list(request, app_label=None):
            app_list = base_get_app_list(request, app_label)
            for app in app_list:
                if app["app_label"] == self.label:
                    app["models"] = [
                        model
                        for model in app["models"]
                        if model["object_name"]
                        in {"Achievement", "ManualAwardAssignment"}
                    ]
                    app["models"].sort(
                        key=lambda model: 0
                        if model["object_name"] == "Achievement"
                        else 1
                    )
            return app_list

        admin.site.get_app_list = get_app_list
