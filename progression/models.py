from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class LevelDefinition(models.Model):
    name = models.CharField(max_length=100, unique=True)
    points_required = models.PositiveIntegerField(unique=True)

    class Meta:
        ordering = ("points_required", "name")
        verbose_name = "nivå"
        verbose_name_plural = "nivåer"

    def clean(self):
        super().clean()
        self.name = (self.name or "").strip()
        if not self.name:
            raise ValidationError({"name": "Nivånamn måste anges."})
        if self.points_required is not None and self.points_required < 0:
            raise ValidationError({"points_required": "Poängkravet kan inte vara negativt."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.points_required} poäng)"


class UserLevelAchievement(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="level_achievements")
    level = models.ForeignKey(LevelDefinition, on_delete=models.PROTECT, related_name="achievements")
    level_name = models.CharField(max_length=100)
    points_required = models.PositiveIntegerField()
    achieved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("points_required", "achieved_at")
        constraints = [
            models.UniqueConstraint(fields=("user", "level"), name="unique_user_level_achievement"),
        ]
        verbose_name = "uppnådd nivå"
        verbose_name_plural = "uppnådda nivåer"

    def __str__(self):
        return f"{self.user}: {self.level_name}"
