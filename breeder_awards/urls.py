"""URL configuration for the Breeder Awards project."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from .views import home
from taxonomy.data_quality_api import random_species_data_quality

urlpatterns = [
    path("", home, name="home"),
    path("api/species/data-quality/random/", random_species_data_quality, name="species_data_quality_random"),
    path("admin/", admin.site.urls),
    path("", include("users.urls")),
    path("", include("associations.urls")),
    path("", include("breedings.urls")),
    path("", include("progression.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
