from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

from taxonomy.models import Genus, SpeciesGroup

from .image_validators import validate_achievement_overlay, validate_award_image_dimensions


hex_color_validator = RegexValidator(
    regex=r"^#[0-9A-Fa-f]{6}$",
    message="Färgen måste anges som #RRGGBB.",
)


class Achievement(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="namn")
    calendar_year_based = models.BooleanField(
        default=False,
        verbose_name="ska uppnås inom kalenderår",
    )
    image = models.ImageField(
        upload_to="achievements/images/",
        blank=True,
        validators=[validate_achievement_overlay],
        verbose_name="utmärkelsebild",
    )
    background_image = models.ImageField(
        upload_to="achievements/custom_backgrounds/",
        blank=True,
        validators=[validate_award_image_dimensions],
        verbose_name="egen bakgrundsbild",
    )

    class Meta:
        ordering = ("name",)
        verbose_name = "utmärkelse"
        verbose_name_plural = "utmärkelser"

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class AchievementBackground(models.Model):
    calendar_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        unique=True,
        verbose_name="kalenderår",
        help_text="Lämna tomt för lifetime-bakgrunden.",
    )
    image = models.ImageField(
        upload_to="achievements/backgrounds/",
        validators=[validate_award_image_dimensions],
        verbose_name="bakgrundsbild",
    )
    tint_color = models.CharField(
        max_length=7,
        blank=True,
        validators=[hex_color_validator],
        verbose_name="färgning",
        help_text="Valfri färg i formatet #RRGGBB. Används bara för års-bakgrunder.",
    )

    class Meta:
        ordering = ("calendar_year",)
        verbose_name = "bakgrund"
        verbose_name_plural = "bakgrunder"

    def clean(self):
        super().clean()
        errors = {}
        if self.calendar_year is None:
            if self.tint_color:
                errors["tint_color"] = "Lifetime-bakgrunden kan inte ha års-färgning."
            lifetime_query = AchievementBackground.objects.filter(calendar_year__isnull=True)
            if self.pk:
                lifetime_query = lifetime_query.exclude(pk=self.pk)
            if lifetime_query.exists():
                errors["calendar_year"] = "Det kan bara finnas en lifetime-bakgrund."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    @classmethod
    def lifetime(cls):
        return cls.objects.filter(calendar_year__isnull=True).first()

    @classmethod
    def for_year(cls, year):
        return cls.objects.filter(calendar_year__lte=year).order_by("-calendar_year").first()

    def __str__(self):
        if self.calendar_year is None:
            return "Lifetime"
        return str(self.calendar_year)


class AchievementLevel(models.Model):
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name="levels",
        verbose_name="utmärkelse",
    )
    name = models.CharField(max_length=15, verbose_name="nivånamn")
    description = models.CharField(max_length=300, blank=True, verbose_name="beskrivning")
    image = models.ImageField(
        upload_to="achievements/level_images/",
        blank=True,
        validators=[validate_achievement_overlay],
        verbose_name="nivåbild",
    )
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
        verbose_name = "nivå"
        verbose_name_plural = "nivåer"

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.achievement}: {self.name}"


class AchievementRequirement(models.Model):
    class Kind(models.TextChoices):
        POINTS = "points", "Poäng"
        BREEDING_COUNT = "breeding_count", "Antal odlingar"
        SPECIES_COUNT = "species_count", "Antal arter"

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
        verbose_name = "krav"
        verbose_name_plural = "krav"

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
    level_description = models.CharField(max_length=300, blank=True)
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
        verbose_name = "uppnådd"
        verbose_name_plural = "uppnådda"

    def __str__(self):
        suffix = f" ({self.calendar_year})" if self.calendar_year else ""
        return f"{self.user}: {self.achievement_name} – {self.level_name}{suffix}"
