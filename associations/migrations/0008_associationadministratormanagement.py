from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("associations", "0007_membership_is_association_admin"),
    ]

    operations = [
        migrations.CreateModel(
            name="AssociationAdministratorManagement",
            fields=[],
            options={
                "verbose_name": "föreningsadministratör",
                "verbose_name_plural": "Föreningsadministratörer",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("associations.membership",),
        ),
    ]
