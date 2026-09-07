from django.urls import path

from .views import AccountLogoutView, EmailLoginView, account, register

urlpatterns = [
    path("accounts/register/", register, name="register"),
    path("accounts/login/", EmailLoginView.as_view(), name="login"),
    path("accounts/logout/", AccountLogoutView.as_view(), name="logout"),
    path("account/", account, name="account"),
]
