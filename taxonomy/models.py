from django.db import models


class Genus(models.Model):
    scientific_name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["scientific_name"]
        verbose_name = "genus"
        verbose_name_plural = "genera"

    def __str__(self):
        return self.scientific_name


class SpeciesGroup(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="namn")

    class Meta:
        ordering = ["name"]
        verbose_name = "artgrupp"
        verbose_name_plural = "artgrupper"

    def __str__(self):
        return self.name
