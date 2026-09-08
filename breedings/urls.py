from django.urls import path

from . import views

urlpatterns = [
    path("topplista/", views.individual_leaderboard, name="individual_leaderboard"),
    path("odlingar/", views.breeding_list, name="breeding_list"),
    path("odlingar/ny/", views.breeding_create, name="breeding_create"),
    path("odlingar/<int:pk>/", views.breeding_detail, name="breeding_detail"),
    path("odlingar/<int:pk>/redigera/", views.breeding_edit, name="breeding_edit"),
    path("odlingar/<int:pk>/aterga-till-utkast/", views.breeding_return_to_draft, name="breeding_return_to_draft"),
]
