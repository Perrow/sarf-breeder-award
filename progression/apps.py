from django.apps import AppConfig


class ProgressionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "progression"
    verbose_name = "Utmärkelser"

    def ready(self):
        from django.contrib import admin

        previous_get_app_list = admin.site.get_app_list

        def get_app_list(request, app_label=None):
            app_list = previous_get_app_list(request, app_label)
            for app in app_list:
                if app["app_label"] == self.label:
                    app["models"] = [
                        model
                        for model in app["models"]
                        if model["object_name"] == "Achievement"
                    ]
            return app_list

        admin.site.get_app_list = get_app_list
