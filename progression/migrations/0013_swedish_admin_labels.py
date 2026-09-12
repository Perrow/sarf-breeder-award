from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


HELP_TEXT = (
    "Tillgängliga platshållare: {current}, {target}, {missing}, {unit}, "
    "{target_unit}, {missing_unit}, {target_text}, {missing_text}, "
    "{scope}, {scope_suffix}. {scope_suffix} innehåller ' inom …' när ett "
    "släkte eller en artgrupp finns, annars tom text."
)


class Migration(migrations.Migration):
    dependencies = [
        ("progression", "0012_alter_achievement_name_alter_achievementlevel_name"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="achievementbackground",
            name="calendar_year",
            field=models.PositiveIntegerField(blank=True, help_text="Lämna tomt för livstidsbakgrunden.", null=True, unique=True, verbose_name="kalenderår"),
        ),
        migrations.AlterField(
            model_name="achievementbackground",
            name="tint_color",
            field=models.CharField(blank=True, help_text="Valfri färg i formatet #RRGGBB. Används bara för årsbakgrunder.", max_length=7, verbose_name="färgning"),
        ),
        migrations.AlterField(
            model_name="achievementrequirement",
            name="genera",
            field=models.ManyToManyField(blank=True, related_name="achievement_requirements", to="taxonomy.genus", verbose_name="släkten"),
        ),
        migrations.AlterField(model_name="requirementtexttemplate", name="achieved_template", field=models.CharField(help_text=HELP_TEXT, max_length=300, verbose_name="uppnådda krav")),
        migrations.AlterField(model_name="requirementtexttemplate", name="next_level_template", field=models.CharField(help_text=HELP_TEXT, max_length=300, verbose_name="till nästa nivå")),
        migrations.AlterField(model_name="userachievement", name="user", field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="achievements", to=settings.AUTH_USER_MODEL, verbose_name="användare")),
        migrations.AlterField(model_name="userachievement", name="level", field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="user_achievements", to="progression.achievementlevel", verbose_name="nivå")),
        migrations.AlterField(model_name="userachievement", name="achievement_name", field=models.CharField(max_length=100, verbose_name="utmärkelse")),
        migrations.AlterField(model_name="userachievement", name="level_name", field=models.CharField(max_length=100, verbose_name="nivånamn")),
        migrations.AlterField(model_name="userachievement", name="level_description", field=models.CharField(blank=True, max_length=300, verbose_name="nivåbeskrivning")),
        migrations.AlterField(model_name="userachievement", name="calendar_year", field=models.PositiveIntegerField(blank=True, null=True, verbose_name="kalenderår")),
        migrations.AlterField(model_name="userachievement", name="achieved_at", field=models.DateTimeField(auto_now_add=True, verbose_name="uppnådd")),
    ]
