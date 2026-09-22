from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models

from breeder_awards.db_collations import CASE_INSENSITIVE_COLLATION


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email=None, password=None, **extra_fields):
        if not email:
            raise ValueError("E-post måste anges.")
        email = self.normalize_email(email).strip().lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser måste ha is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser måste ha is_superuser=True.")

        return self.create_user(email=email, password=password, **extra_fields)


class User(AbstractUser):
    """Application user model."""

    username = None
    first_name = None
    last_name = None

    email = models.EmailField(
        unique=True,
        db_collation=CASE_INSENSITIVE_COLLATION,
        verbose_name="e-post",
    )
    name = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="namn",
    )
    public_username = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        db_collation=CASE_INSENSITIVE_COLLATION,
        verbose_name="användarnamn",
    )
    avatar_url = models.URLField(blank=True, verbose_name="profilbild")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def get_full_name(self):
        return self.name.strip()

    def get_short_name(self):
        return self.name.strip()

    def public_display_name(self):
        """Return a name safe to expose in a public context."""
        return self.public_username or "Användare"
