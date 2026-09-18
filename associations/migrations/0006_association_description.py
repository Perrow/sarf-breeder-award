from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("associations", "0005_association_contact_person_note"),
    ]

    operations = [
        migrations.AddField(
            model_name="association",
            name="description",
            field=models.CharField(blank=True, max_length=500, verbose_name="beskrivning"),
        ),
    ]
