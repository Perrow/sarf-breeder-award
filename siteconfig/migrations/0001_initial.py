from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SiteBranding",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "header_logo",
                    models.ImageField(
                        blank=True,
                        upload_to="site-branding/",
                        verbose_name="logotyp i sidhuvud",
                    ),
                ),
                (
                    "footer_logo",
                    models.ImageField(
                        blank=True,
                        upload_to="site-branding/",
                        verbose_name="logotyp i sidfot",
                    ),
                ),
            ],
            options={
                "verbose_name": "sidprofilering",
                "verbose_name_plural": "sidprofilering",
            },
        ),
    ]
