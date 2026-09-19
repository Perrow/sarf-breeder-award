from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("associations", "0006_association_description"),
    ]

    operations = [
        migrations.AddField(
            model_name="membership",
            name="is_association_admin",
            field=models.BooleanField(default=False, verbose_name="föreningsadministratör"),
        ),
    ]
