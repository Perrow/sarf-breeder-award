from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("associations", "0003_association_website_url"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="association",
            options={"verbose_name": "förening", "verbose_name_plural": "föreningar"},
        ),
        migrations.AlterModelOptions(
            name="membership",
            options={"verbose_name": "medlemskap", "verbose_name_plural": "medlemskap"},
        ),
        migrations.AlterField(model_name="association", name="name", field=models.CharField(max_length=200, verbose_name="namn")),
        migrations.AlterField(model_name="association", name="organization_number", field=models.CharField(blank=True, max_length=50, verbose_name="organisationsnummer")),
        migrations.AlterField(model_name="association", name="email", field=models.EmailField(blank=True, max_length=254, verbose_name="e-post")),
        migrations.AlterField(model_name="association", name="phone", field=models.CharField(blank=True, max_length=50, verbose_name="telefon")),
        migrations.AlterField(model_name="association", name="address", field=models.CharField(blank=True, max_length=255, verbose_name="adress")),
        migrations.AlterField(model_name="association", name="postal_code", field=models.CharField(blank=True, max_length=20, verbose_name="postnummer")),
        migrations.AlterField(model_name="association", name="city", field=models.CharField(blank=True, max_length=100, verbose_name="ort")),
        migrations.AlterField(model_name="association", name="description", field=models.TextField(blank=True, verbose_name="beskrivning")),
        migrations.AlterField(model_name="membership", name="user", field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to=settings.AUTH_USER_MODEL, verbose_name="användare")),
        migrations.AlterField(model_name="membership", name="association", field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to="associations.association", verbose_name="förening")),
        migrations.AlterField(model_name="membership", name="member_number", field=models.CharField(blank=True, max_length=100, verbose_name="medlemsnummer")),
        migrations.AlterField(model_name="membership", name="phone", field=models.CharField(blank=True, max_length=50, verbose_name="telefon")),
        migrations.AlterField(model_name="membership", name="association_data", field=models.TextField(blank=True, verbose_name="föreningsuppgifter")),
    ]
