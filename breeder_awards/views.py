from django.shortcuts import redirect, render


def home(request):
    if request.user.is_authenticated:
        return redirect("breeding_list")
    return render(request, "home.html")
