from django.contrib import admin
from .models import (
    PlayerProfile,
    CoinPackage,
    Dino,
    Transaction,
    Purchase,
    PlayerGameData,
    DinoSlot
)

# ------------------------------
# Customize admin site headers
# ------------------------------
admin.site.site_header = "JURASSIC WORLD COINS Admin"
admin.site.site_title = "JURASSIC WORLD COINS Admin Portal"
admin.site.index_title = "Welcome to the JURASSIC WORLD COINS Dashboard"

# ------------------------------
# Register models
# ------------------------------
admin.site.register(PlayerProfile)
admin.site.register(CoinPackage)
admin.site.register(Dino)
admin.site.register(Transaction)
admin.site.register(Purchase)
admin.site.register(PlayerGameData)
admin.site.register(DinoSlot)
