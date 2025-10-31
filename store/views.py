import re
import json
import stripe
import random
import string
import requests
from urllib.parse import urlencode

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test

from .models import PlayerProfile, PlayerGameData, Dino, DinoSlot, CoinPackage, Transaction
from .forms import DinosaurForm, CoinPackageForm


# ------------------------------------------------------------
# GLOBALS
# ------------------------------------------------------------
stripe.api_key = settings.STRIPE_SECRET_KEY
STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"


# ------------------------------------------------------------
# UTILITIES
# ------------------------------------------------------------
def random_password(length=12):
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(chars) for _ in range(length))


# ------------------------------------------------------------
# STEAM LOGIN / AUTH
# ------------------------------------------------------------
def login_page(request):
    if request.session.get("steam_id"):
        return redirect("store:main_page")
    return render(request, "default.html")


def steam_login(request):
    return_to = request.build_absolute_uri(reverse("store:steam-verify"))
    realm = request.build_absolute_uri("/")

    params = {
        "openid.ns": "http://specs.openid.net/auth/2.0",
        "openid.mode": "checkid_setup",
        "openid.return_to": return_to,
        "openid.realm": realm,
        "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
        "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
    }

    return redirect(f"{STEAM_OPENID_URL}?{urlencode(params)}")


def steam_verify(request):
    data = request.GET.dict()
    if "openid.claimed_id" not in data:
        return HttpResponse("❌ Invalid Steam response")

    data["openid.mode"] = "check_authentication"
    response = requests.post(STEAM_OPENID_URL, data=data)

    if "is_valid:true" in response.text:
        match = re.search(r"https://steamcommunity.com/openid/id/(\d+)", data["openid.claimed_id"])
        if not match:
            return HttpResponse("❌ Steam ID not found")

        steam_id = match.group(1)
        request.session["steam_id"] = steam_id

        user, _ = User.objects.get_or_create(
            username=f"steam_{steam_id}",
            defaults={"password": make_password(random_password())}
        )

        player_profile, _ = PlayerProfile.objects.get_or_create(
            user=user,
            defaults={"steam_id": steam_id}
        )
        PlayerGameData.objects.get_or_create(player=player_profile)

        return redirect("store:main_page")

    return HttpResponse("❌ Steam login verification failed.")


def logout_view(request):
    request.session.flush()
    return redirect("store:login-page")


# ------------------------------------------------------------
# MAIN STORE / PLAYER DASHBOARD
# ------------------------------------------------------------
def main_page(request):
    steam_id = request.session.get("steam_id")
    if not steam_id:
        return redirect("store:login-page")

    player_profile = get_object_or_404(PlayerProfile, steam_id=steam_id)
    dinos = Dino.objects.all()
    packages = CoinPackage.objects.all()
    slots = DinoSlot.objects.filter(player=player_profile)

    context = {
        "player_profile": player_profile,
        "dinos": dinos,
        "packages": packages,
        "coin_balance": player_profile.coins,
        "slots": slots,
    }
    return render(request, "main_page.html", context)



def player_dashboard(request, steam_id):
    player_profile = get_object_or_404(PlayerProfile, steam_id=steam_id)
    player_game_data, _ = PlayerGameData.objects.get_or_create(player=player_profile)

    context = {
        "steam_id": steam_id,
        "player_profile": player_profile,
        "player_game_data": player_game_data,
        "dinos": Dino.objects.all(),
        "coin_balance": player_profile.coins,
    }
    return render(request, "player_dashboard.html", context)


# ------------------------------------------------------------
# PLAYER DINO MANAGEMENT
# ------------------------------------------------------------
def switch_dino(request, slot_id):
    messages.success(request, f"Dino in slot {slot_id} switched successfully.")
    return redirect("store:main_page")


def release_dino(request, slot_id):
    messages.success(request, f"Dino in slot {slot_id} released successfully.")
    return redirect("store:main_page")


def add_dino(request, slot_id):
    slot = get_object_or_404(DinoSlot, id=slot_id)
    dinos = Dino.objects.all()

    if request.method == "POST":
        dino_id = request.POST.get("dino_id")
        dino = get_object_or_404(Dino, id=dino_id)
        slot.active_dino = dino
        slot.save()
        return redirect("store:main_page")

    context = {
        "slot": slot,
        "dinos": dinos
    }
    return render(request, "store/add_dino.html", context)

def buy_dino(request, dino_id):
    steam_id = request.session.get("steam_id")
    if not steam_id:
        return redirect("store:login-page")

    player = get_object_or_404(PlayerProfile, steam_id=steam_id)
    dino = get_object_or_404(Dino, id=dino_id)
    player_game_data, _ = PlayerGameData.objects.get_or_create(player=player)

    if player.coins >= dino.coin_cost:
        player.coins -= dino.coin_cost
        player.save()
        player_game_data.unlocked_dinos.add(dino)
        player_game_data.save()
        messages.success(request, f"You bought {dino.name} successfully!")
    else:
        messages.error(request, "❌ Not enough coins to buy this dinosaur!")

    return redirect("store:main_page")


def release_dino(request, slot_id):
    slot = get_object_or_404(DinoSlot, id=slot_id)
    if slot.active_dino:
        slot.active_dino = None
        slot.save()
    return redirect("store:main_page")

# Switch Dino (choose another dino for the slot)
def switch_dino(request, slot_id):
    slot = get_object_or_404(DinoSlot, id=slot_id)
    dinos = Dino.objects.all()

    if request.method == "POST":
        dino_id = request.POST.get("dino_id")
        dino = get_object_or_404(Dino, id=dino_id)
        slot.active_dino = dino
        slot.save()
        return redirect("store:main_page")

    return render(request, "store/switch_dino.html", {"slot": slot, "dinos": dinos})

# ------------------------------------------------------------
# STRIPE PAYMENT (COINS)
# ------------------------------------------------------------
def buy_coins(request, package_id):
    package = get_object_or_404(CoinPackage, id=package_id)
    steam_id = request.session.get("steam_id")
    if not steam_id:
        return redirect("store:login-page")

    player = get_object_or_404(PlayerProfile, steam_id=steam_id)

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': f"{package.name} — {package.coins_amount} Coins"},
                'unit_amount': int(package.price_usd * 100),
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri(reverse('store:coin_success')) + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=request.build_absolute_uri(reverse('store:coin_cancel')),
        customer_email=player.user.email or None,
    )

    Transaction.objects.create(
        player=player,
        amount_usd=package.price_usd,
        coins_purchased=package.coins_amount,
        status="pending",
    )

    return redirect(session.url, code=303)


def coin_success(request):
    session_id = request.GET.get('session_id')
    return render(request, "coins/success.html", {"session_id": session_id})


def coin_cancel(request):
    messages.warning(request, "Your payment was canceled or not completed.")
    return render(request, "coins/cancel.html")


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        txn = Transaction.objects.filter(
            amount_usd=session['amount_total'] / 100,
            status='pending'
        ).first()

        if txn:
            player = txn.player
            player.coins += txn.coins_purchased
            player.save()
            txn.status = 'completed'
            txn.save()

    return HttpResponse(status=200)


# ------------------------------------------------------------
# ADMIN PANEL
# ------------------------------------------------------------
def is_admin(user):
    return user.is_superuser or user.is_staff


@user_passes_test(is_admin)
def admin_dashboard(request):
    context = {
        'dino_count': Dino.objects.count(),
        'package_count': CoinPackage.objects.count(),
        'player_count': PlayerProfile.objects.count(),
        'dinos': Dino.objects.all(),
        'packages': CoinPackage.objects.all(),
        'players': PlayerProfile.objects.all(),
    }
    return render(request, 'store/admin_dashboard.html', context)


# ------------------------------------------------------------
# ADMIN CRUD (Dinos & Packages)
# ------------------------------------------------------------
@user_passes_test(is_admin)
def add_dino_admin(request):
    if request.method == "POST":
        form = DinosaurForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Dinosaur added successfully!")
            return redirect("store:admin-dashboard")
    else:
        form = DinosaurForm()
    return render(request, "store/admin_form.html", {"form": form, "title": "Add Dinosaur"})


@user_passes_test(is_admin)
def edit_dino_admin(request, dino_id):
    dino = get_object_or_404(Dino, id=dino_id)
    if request.method == "POST":
        form = DinosaurForm(request.POST, request.FILES, instance=dino)
        if form.is_valid():
            form.save()
            messages.success(request, f"{dino.name} updated successfully!")
            return redirect("store:admin-dashboard")
    else:
        form = DinosaurForm(instance=dino)
    return render(request, "store/admin_form.html", {"form": form, "title": "Edit Dinosaur"})


@user_passes_test(is_admin)
def delete_dino_admin(request, dino_id):
    dino = get_object_or_404(Dino, id=dino_id)
    dino.delete()
    messages.success(request, f"{dino.name} deleted successfully!")
    return redirect("store:admin-dashboard")


@user_passes_test(is_admin)
def add_package_admin(request):
    if request.method == "POST":
        form = CoinPackageForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Package added successfully!")
            return redirect("store:admin-dashboard")
    else:
        form = CoinPackageForm()
    return render(request, "store/admin_form.html", {"form": form, "title": "Add Package"})


@user_passes_test(is_admin)
def edit_package_admin(request, package_id):
    package = get_object_or_404(CoinPackage, id=package_id)
    if request.method == "POST":
        form = CoinPackageForm(request.POST, instance=package)
        if form.is_valid():
            form.save()
            messages.success(request, f"{package.name} updated successfully!")
            return redirect("store:admin-dashboard")
    else:
        form = CoinPackageForm(instance=package)
    return render(request, "store/admin_form.html", {"form": form, "title": "Edit Package"})


@user_passes_test(is_admin)
def delete_package_admin(request, package_id):
    package = get_object_or_404(CoinPackage, id=package_id)
    package.delete()
    messages.success(request, f"{package.name} deleted successfully!")
    return redirect("store:admin-dashboard")
