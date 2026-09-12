from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("associations", "0002_membership_phone_and_admin_groups"),
    ]

    operations = [
        migrations.AddField(
            model_name="association",
            name="website_url",
            field=models.URLField(blank=True, max_length=500, verbose_name="hemsida"),
        ),
    ]
