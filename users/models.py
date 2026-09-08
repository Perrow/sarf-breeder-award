from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Application user model."""

    display_name = models.CharField(max_length=150, blank=True, verbose_name="visningsnamn")
    location = models.CharField(max_length=150, blank=True, verbose_name="ort")
    avatar_url = models.URLField(blank=True, verbose_name="profilbild")
