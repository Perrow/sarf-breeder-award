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
                        in {"Achievement", "AchievementBackground", "ManualAwardAssignment"}
                    ]
                    menu_order = {
                        "Achievement": 0,
                        "AchievementBackground": 1,
                        "ManualAwardAssignment": 2,
                    }
                    app["models"].sort(
                        key=lambda model: menu_order[model["object_name"]]
                    )
            return app_list

        admin.site.get_app_list = get_app_list
