from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from urllib.parse import urlencode
import requests, re

# Steam OpenID endpoint
STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"


# 1️⃣ Show login page
def login_page(request):
    return render(request, "login.html")


# 2️⃣ Redirect to Steam login
def steam_login(request):
    return_to = request.build_absolute_uri(reverse("steam-verify"))
    realm = request.build_absolute_uri("/")

    params = {
        "openid.ns": "http://specs.openid.net/auth/2.0",
        "openid.mode": "checkid_setup",
        "openid.return_to": return_to,
        "openid.realm": realm,
        "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
        "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
    }

    steam_redirect_url = f"{STEAM_OPENID_URL}?{urlencode(params)}"
    return redirect(steam_redirect_url)


# 3️⃣ Handle Steam response
def steam_verify(request):
    data = request.GET.dict()

    if "openid.claimed_id" not in data:
        return HttpResponse("❌ Invalid Steam response")

    data["openid.mode"] = "check_authentication"
    response = requests.post(STEAM_OPENID_URL, data=data)

    if "is_valid:true" in response.text:
        match = re.search(r"https://steamcommunity.com/openid/id/(\d+)", data["openid.claimed_id"])
        if match:
            steam_id = match.group(1)
            return render(request, "login_success.html", {"steam_id": steam_id})

    return HttpResponse("❌ Steam login verification failed.")
