from .permissions import is_association_admin, is_system_admin


def association_admin_access(request):
    user = getattr(request, "user", None)
    return {
        "can_manage_associations": (
            is_system_admin(user) or is_association_admin(user)
        )
    }
