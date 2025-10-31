import stripe
import json
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Initialize Stripe with your secret key
stripe.api_key = settings.STRIPE_SECRET_KEY


# 🏠 Main Page (checks login status)
def main_page(request):
    """
    Render the homepage:
      - If user is logged in → show store page (main.html)
      - If not logged in → show default.html
    """
    if not request.user.is_authenticated:
        return render(request, "default.html")
    else:
        return render(request, "main.html", {
            "stripe_pub_key": settings.STRIPE_PUBLISHABLE_KEY
        })


# 💳 Create Stripe Checkout Session
@csrf_exempt
def create_checkout_session(request):
    """
    Creates a Stripe Checkout session for purchasing coins.
    Expects JSON data like: {"package": "500_coins"}
    """
    try:
        data = json.loads(request.body)
        package = data.get("package", "500_coins")

        # Map your package names to actual Stripe Price IDs
        price_lookup = {
            "500_coins": "price_XXXX",  # TODO: replace with your real Stripe price ID
            "1000_coins": "price_YYYY",  # Add more packages if needed
        }

        price_id = price_lookup.get(package)
        if not price_id:
            return JsonResponse({"error": "Invalid package"}, status=400)

        # Create Stripe session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{"price": price_id, "quantity": 1}],
            mode='payment',
            success_url=request.build_absolute_uri("/payments/success/"),
            cancel_url=request.build_absolute_uri("/payments/cancel/"),
        )

        return JsonResponse({"sessionId": session.id})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ✅ Payment Success Page
@login_required
def payment_success(request):
    return render(request, "payment_success.html")


# ❌ Payment Cancel Page
def payment_cancel(request):
    return render(request, "payment_cancel.html")
