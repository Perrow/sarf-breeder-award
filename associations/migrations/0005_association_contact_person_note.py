from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("associations", "0004_swedish_admin_labels"),
    ]

    operations = [
        migrations.RenameField(
            model_name="association",
            old_name="description",
            new_name="note",
        ),
        migrations.AlterField(
            model_name="association",
            name="note",
            field=models.TextField(blank=True, verbose_name="anteckning"),
        ),
        migrations.AddField(
            model_name="association",
            name="contact_person",
            field=models.CharField(blank=True, max_length=200, verbose_name="kontaktperson"),
        ),
    ]
