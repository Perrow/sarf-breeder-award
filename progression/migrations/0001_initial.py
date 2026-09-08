from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="LevelDefinition",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("points_required", models.PositiveIntegerField(unique=True)),
            ],
            options={"verbose_name": "nivå", "verbose_name_plural": "nivåer", "ordering": ("points_required", "name")},
        ),
        migrations.CreateModel(
            name="UserLevelAchievement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("level_name", models.CharField(max_length=100)),
                ("points_required", models.PositiveIntegerField()),
                ("achieved_at", models.DateTimeField(auto_now_add=True)),
                ("level", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="achievements", to="progression.leveldefinition")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="level_achievements", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "uppnådd nivå", "verbose_name_plural": "uppnådda nivåer", "ordering": ("points_required", "achieved_at")},
        ),
        migrations.AddConstraint(
            model_name="userlevelachievement",
            constraint=models.UniqueConstraint(fields=("user", "level"), name="unique_user_level_achievement"),
        ),
    ]
