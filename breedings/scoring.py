from taxonomy.models import Species

from .models import BreedingRegistration


BREEDING_CLASS_POINTS = {
    Species.BreedingClass.BRONZE: 1,
    Species.BreedingClass.SILVER: 2,
    Species.BreedingClass.GOLD: 3,
}


def points_for_breeding_class(breeding_class):
    """Return points for a valid breeding class."""
    try:
        return BREEDING_CLASS_POINTS[breeding_class]
    except KeyError as exc:
        raise ValueError("Ogiltig odlingsklass.") from exc


def points_for_registration(registration):
    """Return points for an approved registration, otherwise None."""
    if registration.status != BreedingRegistration.Status.APPROVED:
        return None
    if not registration.awarded_breeding_class:
        return None
    return points_for_breeding_class(registration.awarded_breeding_class)


def career_points(user):
    """Return career points, counting each species at most once."""
    best_points_by_species = {}
    registrations = BreedingRegistration.objects.filter(
        owner=user,
        status=BreedingRegistration.Status.APPROVED,
        species__isnull=False,
    ).only("species_id", "status", "awarded_breeding_class")

    for registration in registrations:
        points = points_for_registration(registration)
        if points is None:
            continue
        best_points_by_species[registration.species_id] = max(
            points,
            best_points_by_species.get(registration.species_id, 0),
        )

    return sum(best_points_by_species.values())
