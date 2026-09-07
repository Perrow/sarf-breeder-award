from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Application user model.

    BA-002 intentionally introduces no additional fields. Using a project-owned
    model from the start allows later tasks to extend users without replacing
    Django's built-in user table after migrations have been applied.
    """

    pass
