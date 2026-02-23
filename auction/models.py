from django.db import models

# --- Team Model ---
class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    owner = models.CharField(max_length=100)
    purse_remaining = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name

# --- Player Model ---
class Player(models.Model):
    # Choices for Player Type
    Defender = 'Def'
    Forward = 'For'
    Goalkeeper = 'Goal'
    Midfielder = 'Mid'

    PLAYER_TYPES = [
        (Defender, 'Defender'),
        (Forward, 'Forward'),
        (Goalkeeper, 'Goalkeeper'),
        (Midfielder, 'Midfielder'),
    ]

    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    photo = models.ImageField(upload_to='player_photos/', null=True, blank=True)
    player_type = models.CharField(max_length=4, choices=PLAYER_TYPES)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_sold = models.BooleanField(default=False)
    sold_to_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.name


class AuctionStatus(models.Model):
    current_player = models.OneToOneField(Player, on_delete=models.SET_NULL, null=True, blank=True)
    current_bid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    current_bid_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=False) # True when auction is running

    # Use a class method to get the single instance of the status
    @classmethod
    def get_instance(cls):
        # Creates the instance if it doesn't exist, otherwise returns the existing one
        return cls.objects.get_or_create(pk=1)[0]
