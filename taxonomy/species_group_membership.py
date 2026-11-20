"""Associate new genera with the groups defined by data migration 0016."""

from importlib import import_module

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Genus, SpeciesGroup


GROUP_GENERA = import_module(
    "taxonomy.migrations.0016_populate_additional_species_groups"
).GROUP_GENERA

GROUPS_BY_GENUS = {}
for group_name, genus_names in GROUP_GENERA.items():
    for genus_name in genus_names:
        GROUPS_BY_GENUS.setdefault(genus_name.casefold(), []).append(group_name)


@receiver(post_save, sender=Genus, dispatch_uid="taxonomy_add_default_species_groups")
def add_default_species_groups(sender, instance, created, using, **kwargs):
    if not created:
        return
    group_names = GROUPS_BY_GENUS.get(instance.scientific_name.casefold(), ())
    if not group_names:
        return
    for group in SpeciesGroup.objects.using(using).filter(name__in=group_names):
        group.genera.add(instance)
