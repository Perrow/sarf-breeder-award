from .review import can_review_breedings


def breeding_review_access(request):
    user = getattr(request, "user", None)
    return {"can_review_breedings": can_review_breedings(user)}
