from .models import Association, Membership

SYSTEM_ADMIN_GROUP = "Systemadministratör"


def is_system_admin(user):
    return user.is_superuser or user.groups.filter(name=SYSTEM_ADMIN_GROUP).exists()


def is_association_admin(user, association=None):
    memberships = Membership.objects.filter(
        user=user,
        is_association_admin=True,
    )
    if association is not None:
        memberships = memberships.filter(association=association)
    return memberships.exists()


def can_manage_association(user, association):
    return is_system_admin(user) or is_association_admin(user, association)


def managed_associations(user):
    if is_system_admin(user):
        return Association.objects.all()
    return Association.objects.filter(
        memberships__user=user,
        memberships__is_association_admin=True,
    ).distinct()
