from django.urls import path

from . import delete_actions, report_detail, species_search, user_actions, views

urlpatterns = [
    path("topplistor/", views.leaderboards, name="leaderboards"),
    path("topplista/", views.individual_leaderboard, name="individual_leaderboard"),
    path("foreningstopplista/", views.association_leaderboard, name="association_leaderboard"),
    path(
        "foreningstopplista/regler/",
        views.association_scoring_rules,
        name="association_scoring_rules",
    ),
    path(
        "foreningstopplista/<int:association_id>/medlemmar/",
        views.association_member_leaderboard,
        name="association_member_leaderboard",
    ),
    path(
        "foreningstopplista/<int:association_id>/medlemmar/<int:user_id>/odlingar/",
        views.association_member_breeding_list,
        name="association_member_breeding_list",
    ),
    path("arter/", species_search.species_catalogue, name="species_catalogue"),
    path("arter/<int:pk>/", species_search.species_information, name="species_information"),
    path("odlingar/", views.breeding_list, name="breeding_list"),
    path("odlingar/valj-art/", species_search.species_select, name="species_select"),
    path("odlingar/artsok/", species_search.species_search_results, name="species_search_results"),
    path("odlingar/ny/", views.breeding_create, name="breeding_create"),
    path("odlingar/<int:pk>/", report_detail.breeding_detail, name="breeding_detail"),
    path("odlingar/<int:pk>/redigera/", user_actions.breeding_edit, name="breeding_edit"),
    path("odlingar/<int:pk>/ta-bort/", delete_actions.breeding_delete, name="breeding_delete"),
    path("odlingar/<int:pk>/aterga-till-utkast/", views.breeding_return_to_draft, name="breeding_return_to_draft"),
]
