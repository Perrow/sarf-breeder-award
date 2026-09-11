from django.db import migrations


def ensure_public_usernames(apps, schema_editor):
    User = apps.get_model("users", "User")
    for user in User.objects.filter(public_username__isnull=True).order_by("pk"):
        base = f"anvandare-{user.pk}"
        candidate = base
        suffix = 2
        while User.objects.filter(public_username=candidate).exclude(pk=user.pk).exists():
            candidate = f"{base}-{suffix}"
            suffix += 1
        user.public_username = candidate
        user.save(update_fields=("public_username",))

    for user in User.objects.filter(public_username="").order_by("pk"):
        base = f"anvandare-{user.pk}"
        candidate = base
        suffix = 2
        while User.objects.filter(public_username=candidate).exclude(pk=user.pk).exists():
            candidate = f"{base}-{suffix}"
            suffix += 1
        user.public_username = candidate
        user.save(update_fields=("public_username",))


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0003_user_public_username"),
    ]

    operations = [
        migrations.RunPython(ensure_public_usernames, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="user",
            name="display_name",
        ),
    ]
