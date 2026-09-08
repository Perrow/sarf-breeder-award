from django.urls import path

from . import views

urlpatterns = [
    path("odlingar/", views.breeding_list, name="breeding_list"),
    path("odlingar/ny/", views.breeding_create, name="breeding_create"),
    path("odlingar/<int:pk>/redigera/", views.breeding_edit, name="breeding_edit"),
]
