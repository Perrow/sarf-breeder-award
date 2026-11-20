from django.db import migrations, models
import associations.models


class Migration(migrations.Migration):
    dependencies = [
        ("associations", "0008_associationadministratormanagement"),
    ]

    operations = [
        migrations.AddField(
            model_name="association",
            name="facebook_url",
            field=models.URLField(blank=True, max_length=500, validators=[associations.models.validate_facebook_url], verbose_name="Facebook"),
        ),
        migrations.AddField(
            model_name="association",
            name="instagram_url",
            field=models.URLField(blank=True, max_length=500, validators=[associations.models.validate_instagram_url], verbose_name="Instagram"),
        ),
    ]
