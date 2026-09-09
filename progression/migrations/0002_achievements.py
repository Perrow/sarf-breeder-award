from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("progression", "0001_initial"),
        ("taxonomy", "0007_speciesgroup_is_visible"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Achievement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True, verbose_name="namn")),
                ("calendar_year_based", models.BooleanField(default=False, verbose_name="ska uppnås inom kalenderår")),
            ],
            options={"ordering": ("name",), "verbose_name": "utmärkelse", "verbose_name_plural": "utmärkelser"},
        ),
        migrations.CreateModel(
            name="AchievementLevel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, verbose_name="nivånamn")),
                ("order", models.PositiveIntegerField(verbose_name="ordning")),
                ("achievement", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="levels", to="progression.achievement", verbose_name="utmärkelse")),
            ],
            options={"ordering": ("achievement__name", "order", "name"), "verbose_name": "utmärkelsenivå", "verbose_name_plural": "utmärkelsenivåer"},
        ),
        migrations.CreateModel(
            name="AchievementRequirement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("points", "Poäng"), ("breeding_count", "Antal odlingar")], max_length=20, verbose_name="kravtyp")),
                ("value", models.PositiveIntegerField(verbose_name="kravvärde")),
                ("genera", models.ManyToManyField(blank=True, related_name="achievement_requirements", to="taxonomy.genus", verbose_name="genera")),
                ("species_groups", models.ManyToManyField(blank=True, related_name="achievement_requirements", to="taxonomy.speciesgroup", verbose_name="artgrupper")),
                ("level", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="requirements", to="progression.achievementlevel", verbose_name="nivå")),
            ],
            options={"ordering": ("level", "pk"), "verbose_name": "utmärkelsekrav", "verbose_name_plural": "utmärkelsekrav"},
        ),
        migrations.CreateModel(
            name="UserAchievement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("achievement_name", models.CharField(max_length=100)),
                ("level_name", models.CharField(max_length=100)),
                ("calendar_year", models.PositiveIntegerField(blank=True, null=True)),
                ("achieved_at", models.DateTimeField(auto_now_add=True)),
                ("level", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="user_achievements", to="progression.achievementlevel")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="achievements", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("achievement_name", "calendar_year", "level__order", "achieved_at"), "verbose_name": "uppnådd utmärkelse", "verbose_name_plural": "uppnådda utmärkelser"},
        ),
        migrations.AddConstraint(model_name="achievementlevel", constraint=models.UniqueConstraint(fields=("achievement", "order"), name="unique_achievement_level_order")),
        migrations.AddConstraint(model_name="achievementlevel", constraint=models.UniqueConstraint(fields=("achievement", "name"), name="unique_achievement_level_name")),
        migrations.AddConstraint(model_name="userachievement", constraint=models.UniqueConstraint(condition=models.Q(("calendar_year__isnull", True)), fields=("user", "level"), name="unique_lifetime_user_achievement")),
        migrations.AddConstraint(model_name="userachievement", constraint=models.UniqueConstraint(condition=models.Q(("calendar_year__isnull", False)), fields=("user", "level", "calendar_year"), name="unique_yearly_user_achievement")),
        migrations.DeleteModel(name="UserLevelAchievement"),
        migrations.DeleteModel(name="LevelDefinition"),
    ]
