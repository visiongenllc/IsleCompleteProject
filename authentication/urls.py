from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_page, name="login-page"),  # <--- renders login.html
    path("login/", views.steam_login, name="steam-login"),
    path("verify/", views.steam_verify, name="steam-verify"),
]
