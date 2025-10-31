from django.urls import path
from . import views

app_name = "store"

urlpatterns = [
    # ------------------------------
    # Steam Login / Logout
    # ------------------------------
    path('', views.login_page, name='login-page'),
    path('login/', views.steam_login, name='steam-login'),
    path('verify/', views.steam_verify, name='steam-verify'),
    path('logout/', views.logout_view, name='logout'),

    # ------------------------------
    # Main Store / Player Dashboard
    # ------------------------------
    path('main/', views.main_page, name='main_page'),
    path('dashboard/<str:steam_id>/', views.player_dashboard, name='player_dashboard'),

    # ------------------------------
    # Player Dino Management
    # ------------------------------
    path('dino/switch/<int:slot_id>/', views.switch_dino, name='switch_dino'),
    path('dino/release/<int:slot_id>/', views.release_dino, name='release_dino'),
    path('dino/add/<int:slot_id>/', views.add_dino, name='add_dino'),
    path('buy-dino/<int:dino_id>/', views.buy_dino, name='buy_dino'),
    # path("dino/release/<int:slot_id>/", views.release_dino, name="release_dino"),
    # path("dino/switch/<int:slot_id>/", views.switch_dino, name="switch_dino"),

    # ------------------------------
    # Stripe Coin Purchase
    # ------------------------------
    path('coins/buy/<int:package_id>/', views.buy_coins, name='buy_coins'),
    path('coins/success/', views.coin_success, name='coin_success'),
    path('coins/cancel/', views.coin_cancel, name='coin_cancel'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),

    # ------------------------------
    # Admin Panel
    # ------------------------------
    path('admin-panel/', views.admin_dashboard, name='admin-dashboard'),

    # ------------------------------
    # Admin CRUD — Dinosaurs
    # ------------------------------
    path('admin/dino/add/', views.add_dino_admin, name='add_dino_admin'),
    path('admin/dino/edit/<int:dino_id>/', views.edit_dino_admin, name='edit_dino_admin'),
    path('admin/dino/delete/<int:dino_id>/', views.delete_dino_admin, name='delete_dino_admin'),

    # ------------------------------
    # Admin CRUD — Coin Packages
    # ------------------------------
    path('admin/package/add/', views.add_package_admin, name='add_package_admin'),
    path('admin/package/edit/<int:package_id>/', views.edit_package_admin, name='edit_package_admin'),
    path('admin/package/delete/<int:package_id>/', views.delete_package_admin, name='delete_package_admin'),
]
