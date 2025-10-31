from django.db import models
from django.contrib.auth.models import User

# ------------------------------
# Player Profile (connected to Steam)
# ------------------------------
class PlayerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    steam_id = models.CharField(max_length=50, unique=True)
    steam_name = models.CharField(max_length=100, blank=True, null=True, default="")
    avatar_url = models.URLField(blank=True, null=True)  # For Steam avatar
    avatar_image = models.ImageField(
        upload_to="player_avatars/", blank=True, null=True
    )  # Custom uploaded avatar
    coins = models.PositiveIntegerField(default=0)  # Player coin balance

    def __str__(self):
        return self.user.username

# ------------------------------
# Coin Packages (for purchase)
# ------------------------------
class CoinPackage(models.Model):
    name = models.CharField(max_length=50)
    coins_amount = models.PositiveIntegerField(default=2)  
    price_usd = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.name} ({self.coins_amount} coins - ${self.price_usd})"


# ------------------------------
# Dinos in the Store
# ------------------------------
# store/models.py
class Dino(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to="dinos/", null=True, blank=True)
    coin_cost = models.PositiveIntegerField(default=1)  # Default 1 coin
    gender = models.CharField(max_length=20, null=True, blank=True)

    def save(self, *args, **kwargs):
        # Set special dinos to cost 2 coins
        special_dinos = ["Tyrannosaurus rex", "Spinosaurus", "Gigantspinosaurus", "Triceratops"]
        if self.name in special_dinos:
            self.coin_cost = 2
        else:
            self.coin_cost = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name



class CoinPackage(models.Model):
    name = models.CharField(max_length=50)
    price_usd = models.FloatField(default=2.0)  # Coins cost $2 each
    coins_amount = models.PositiveIntegerField(default=1)  # Number of coins the package gives

    def __str__(self):
        return f"{self.name} — ${self.price_usd}"

# ------------------------------
# Coins Transactions (purchases via Stripe or admin)
# ------------------------------
class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    ]

    player = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE)
    amount_usd = models.DecimalField(max_digits=10, decimal_places=2)
    coins_purchased = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Txn #{self.id} - {self.player.user.username}"


# ------------------------------
# Purchased Dinos
# ------------------------------
class Purchase(models.Model):
    player = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE)
    dino = models.ForeignKey(Dino, on_delete=models.CASCADE, null=True, blank=True)
    used_coins = models.PositiveIntegerField(default=0)  # coins spent to grow/buy dino
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        dino_name = self.dino.name if self.dino else "Unknown"
        return f"{self.player.user.username} bought/grew {dino_name}"


# ------------------------------
# Player Game Data (dashboard info)
# ------------------------------
class PlayerGameData(models.Model):
    player = models.OneToOneField(PlayerProfile, on_delete=models.CASCADE)
    total_slots = models.PositiveIntegerField(default=0)
    unlocked_slots = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=50, default="Inactive")
    tier = models.CharField(max_length=100, default="Basic")
    plan_expiry = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.player.user.username} - {self.status}"

class DinoSlot(models.Model):
    player = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="slots")
    server_name = models.CharField(max_length=100)
    active_dino = models.ForeignKey(Dino, null=True, blank=True, on_delete=models.SET_NULL)
    
    # Optional fields if you want to store the stats
    growth = models.PositiveIntegerField(default=0)
    health = models.PositiveIntegerField(default=100)
    stamina = models.PositiveIntegerField(default=100)
    hunger = models.PositiveIntegerField(default=100)
    thirst = models.PositiveIntegerField(default=100)

    def __str__(self):
        return f"{self.player.user.username} — {self.server_name}"
