from django.db import migrations, models


CLASS_CHOICES = [
    ("bronze", "Brons"),
    ("silver", "Silver"),
    ("gold", "Guld"),
    ("elite", "Elit"),
    ("unrated", "Ej bedömd"),
]


class Migration(migrations.Migration):
    dependencies = [
        ("breedings", "0012_breeding_publication_status"),
        ("taxonomy", "0015_elite_unrated_breeding_classes"),
    ]

    operations = [
        migrations.AlterField(
            model_name="breedingregistration",
            name="awarded_breeding_class",
            field=models.CharField(
                blank=True,
                choices=CLASS_CHOICES,
                max_length=10,
                verbose_name="tilldelad odlingsklass",
            ),
        ),
        migrations.AlterField(
            model_name="speciesreclassificationrequest",
            name="current_breeding_class",
            field=models.CharField(
                choices=CLASS_CHOICES,
                max_length=10,
                verbose_name="klass vid begäran",
            ),
        ),
        migrations.AlterField(
            model_name="speciesreclassificationrequest",
            name="requested_breeding_class",
            field=models.CharField(
                choices=CLASS_CHOICES,
                max_length=10,
                verbose_name="önskad klass",
            ),
        ),
    ]
