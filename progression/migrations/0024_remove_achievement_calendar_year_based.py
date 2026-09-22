from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("progression", "0023_backfill_self_selected_requirements"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="achievement",
            name="calendar_year_based",
        ),
    ]
