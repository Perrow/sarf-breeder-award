from django.urls import path

from . import views

urlpatterns = [
    path("foreningsadministration/", views.association_management, name="association_management"),
    path("foreningsadministration/<int:pk>/", views.association_edit, name="association_edit"),
    path(
        "foreningsadministration/<int:pk>/administratorer/",
        views.association_admins,
        name="association_admins",
    ),
    path(
        "systemadministration/foreningsadministratorer/",
        views.system_association_admins,
        name="system_association_admins",
    ),
]
