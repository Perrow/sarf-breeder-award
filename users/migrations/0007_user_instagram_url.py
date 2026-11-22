from django.db import migrations, models
import associations.models


class Migration(migrations.Migration):
    dependencies = [("users", "0006_simplify_user_identity")]

    operations = [
        migrations.AddField(
            model_name="user",
            name="instagram_url",
            field=models.URLField(
                max_length=500, blank=True,
                validators=[associations.models.validate_instagram_url],
                verbose_name="Instagram",
            ),
        ),
    ]
