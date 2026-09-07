from django.utils import translation


class SiteLanguageMiddleware:
    """Use Swedish on the public site while keeping Django admin in English."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        language = "en" if request.path.startswith("/admin/") else "sv"
        with translation.override(language):
            return self.get_response(request)
