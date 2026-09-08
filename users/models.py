from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Application user model."""

    display_name = models.CharField(max_length=150, blank=True, verbose_name="visningsnamn")
    public_username = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        verbose_name="publikt användarnamn",
    )
    location = models.CharField(max_length=150, blank=True, verbose_name="ort")
    avatar_url = models.URLField(blank=True, verbose_name="profilbild")

    def public_display_name(self, profile_information_is_public=False):
        """Return a name safe to expose in a public context."""
        if profile_information_is_public:
            profile_name = (self.display_name or self.get_full_name()).strip()
            if profile_name:
                return profile_name
        return self.public_username or "Användare"
