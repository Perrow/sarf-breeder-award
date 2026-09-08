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
