import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import progression.image_validators


class Migration(migrations.Migration):

    dependencies = [
        ("progression", "0015_demerit_badges"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="DeMeritBadge",
            new_name="SelfmadeBadge",
        ),
        migrations.RenameModel(
            old_name="UserDeMeritBadge",
            new_name="UserSelfmadeBadge",
        ),
        migrations.RemoveConstraint(
            model_name="userselfmadebadge",
            name="unique_user_demerit_badge",
        ),
        migrations.AlterModelOptions(
            name="selfmadebadge",
            options={
                "ordering": ("name",),
                "verbose_name": "egenvald utmärkelse",
                "verbose_name_plural": "egenvalda utmärkelser",
            },
        ),
        migrations.AlterModelOptions(
            name="userselfmadebadge",
            options={
                "ordering": ("-awarded_at", "badge__name", "pk"),
                "verbose_name": "egenvald utmärkelse",
                "verbose_name_plural": "egenvalda utmärkelser",
            },
        ),
        migrations.AlterField(
            model_name="selfmadebadge",
            name="image",
            field=models.ImageField(
                blank=True,
                upload_to="achievements/selfmade/",
                validators=[progression.image_validators.validate_achievement_overlay],
                verbose_name="märkesbild",
            ),
        ),
        migrations.AlterField(
            model_name="userselfmadebadge",
            name="badge",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="grants",
                to="progression.selfmadebadge",
                verbose_name="egenvald utmärkelse",
            ),
        ),
        migrations.AlterField(
            model_name="userselfmadebadge",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="selfmade_badges",
                to=settings.AUTH_USER_MODEL,
                verbose_name="användare",
            ),
        ),
        migrations.AlterField(
            model_name="userselfmadebadge",
            name="awarded_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="egenvald"),
        ),
        migrations.AddConstraint(
            model_name="userselfmadebadge",
            constraint=models.UniqueConstraint(
                fields=("user", "badge"),
                name="unique_user_selfmade_badge",
            ),
        ),
    ]
