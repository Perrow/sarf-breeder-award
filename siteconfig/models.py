from django.db import models


class SiteBranding(models.Model):
    header_logo = models.ImageField(
        upload_to="site-branding/",
        blank=True,
        verbose_name="logotyp i sidhuvud",
    )
    footer_logo = models.ImageField(
        upload_to="site-branding/",
        blank=True,
        verbose_name="logotyp i sidfot",
    )

    class Meta:
        verbose_name = "sidprofilering"
        verbose_name_plural = "sidprofilering"

    def __str__(self):
        return "Sidprofilering"
