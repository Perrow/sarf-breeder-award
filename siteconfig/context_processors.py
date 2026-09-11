from .models import SiteBranding


def site_branding(request):
    return {"site_branding": SiteBranding.objects.first()}
