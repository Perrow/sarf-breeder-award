from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("associations", "0008_associationadministratormanagement"),
        ("progression", "0021_fix_level_name_and_explicit_requirements"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="userachievement",
            name="awarded_association",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="awarded_user_achievements",
                to="associations.association",
                verbose_name="utdelande förening",
            ),
        ),
        migrations.AddField(
            model_name="userachievement",
            name="awarded_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="awarded_user_achievements",
                to=settings.AUTH_USER_MODEL,
                verbose_name="utdelad av",
            ),
        ),
    ]
