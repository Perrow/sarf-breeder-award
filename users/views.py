from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from progression.services import all_achievement_presentations_for_user

from .forms import EmailAuthenticationForm, ProfileForm, RegistrationForm


def register(request):
    if request.user.is_authenticated:
        return redirect("account")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("account")
    else:
        form = RegistrationForm()

    return render(request, "users/register.html", {"form": form})


class EmailLoginView(LoginView):
    authentication_form = EmailAuthenticationForm
    template_name = "users/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return self.get_redirect_url() or reverse_lazy("breeding_list")


class AccountLogoutView(LogoutView):
    next_page = reverse_lazy("login")


@login_required
def account(request):
    memberships = request.user.memberships.select_related("association").order_by("association__name")
    return render(request, "users/account.html", {"memberships": memberships})


@login_required
def account_edit(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profilen har sparats.")
            return redirect("account")
    else:
        form = ProfileForm(instance=request.user)

    return render(request, "users/account_edit.html", {"form": form})


@login_required
def achievements(request):
    presentations = all_achievement_presentations_for_user(request.user)
    return render(
        request,
        "users/achievements.html",
        {
            "career_achievements": presentations["career"],
            "yearly_achievement_groups": presentations["yearly"],
        },
    )
