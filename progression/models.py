from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from taxonomy.models import Genus, SpeciesGroup


class Achievement(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="namn")
    calendar_year_based = models.BooleanField(
        default=False,
        verbose_name="ska uppnås inom kalenderår",
    )

    class Meta:
        ordering = ("name",)
        verbose_name = "utmärkelse"
        verbose_name_plural = "utmärkelser"

    def __str__(self):
        return self.name


class AchievementLevel(models.Model):
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name="levels",
        verbose_name="utmärkelse",
    )
    name = models.CharField(max_length=100, verbose_name="nivånamn")
    order = models.PositiveIntegerField(verbose_name="ordning")

    class Meta:
        ordering = ("achievement__name", "order", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("achievement", "order"),
                name="unique_achievement_level_order",
            ),
            models.UniqueConstraint(
                fields=("achievement", "name"),
                name="unique_achievement_level_name",
            ),
        ]
        verbose_name = "utmärkelsenivå"
        verbose_name_plural = "utmärkelsenivåer"

    def __str__(self):
        return f"{self.achievement}: {self.name}"


class AchievementRequirement(models.Model):
    class Kind(models.TextChoices):
        POINTS = "points", "Poäng"
        BREEDING_COUNT = "breeding_count", "Antal odlingar"

    level = models.ForeignKey(
        AchievementLevel,
        on_delete=models.CASCADE,
        related_name="requirements",
        verbose_name="nivå",
    )
    kind = models.CharField(max_length=20, choices=Kind.choices, verbose_name="kravtyp")
    value = models.PositiveIntegerField(verbose_name="kravvärde")
    genera = models.ManyToManyField(
        Genus,
        blank=True,
        related_name="achievement_requirements",
        verbose_name="genera",
    )
    species_groups = models.ManyToManyField(
        SpeciesGroup,
        blank=True,
        related_name="achievement_requirements",
        verbose_name="artgrupper",
    )

    class Meta:
        ordering = ("level", "pk")
        verbose_name = "utmärkelsekrav"
        verbose_name_plural = "utmärkelsekrav"

    def clean(self):
        super().clean()
        if self.value is not None and self.value < 1:
            raise ValidationError({"value": "Kravvärdet måste vara minst 1."})


class UserAchievement(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="achievements",
    )
    level = models.ForeignKey(
        AchievementLevel,
        on_delete=models.PROTECT,
        related_name="user_achievements",
    )
    achievement_name = models.CharField(max_length=100)
    level_name = models.CharField(max_length=100)
    calendar_year = models.PositiveIntegerField(null=True, blank=True)
    achieved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = (
            "achievement_name",
            "calendar_year",
            "level__order",
            "achieved_at",
        )
        constraints = [
            models.UniqueConstraint(
                fields=("user", "level"),
                condition=models.Q(calendar_year__isnull=True),
                name="unique_lifetime_user_achievement",
            ),
            models.UniqueConstraint(
                fields=("user", "level", "calendar_year"),
                condition=models.Q(calendar_year__isnull=False),
                name="unique_yearly_user_achievement",
            ),
        ]
        verbose_name = "uppnådd utmärkelse"
        verbose_name_plural = "uppnådda utmärkelser"

    def __str__(self):
        suffix = f" ({self.calendar_year})" if self.calendar_year else ""
        return f"{self.user}: {self.achievement_name} – {self.level_name}{suffix}"
