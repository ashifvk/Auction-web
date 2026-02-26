from django.db import models

# --- Team Model ---
class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    owner = models.CharField(max_length=100)
    purse_remaining = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name

    def get_max_bid_amount(self):
        # Calculate the maximum bid amount based on the remaining purse
        settings = Settings.get_instance()  # Ensure settings are loaded
        max_bid_amount = self.purse_remaining
        players_count = self.players.count()
        remaining_palyers = settings.team_capacity - players_count - 1
        amount = max_bid_amount - (remaining_palyers * settings.base_price)
        return max(0, amount)

    def can_bid(self, amount):
        return amount <= self.get_max_bid_amount() and amount <= self.purse_remaining
    
    def can_acquire_player(self):
        settings = Settings.get_instance()
        return self.players.count() < settings.team_capacity
    


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
    sold_to_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='players')
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    random_row = models.FloatField(default=0.0) # Used for random initial ordering
    auction_round = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.name


class AuctionStatus(models.Model):
    current_player = models.OneToOneField(Player, on_delete=models.SET_NULL, null=True, blank=True)
    current_bid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    current_bid_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_bids')
    is_active = models.BooleanField(default=False) # True when auction is running

    # Previous state for undo
    previous_bid_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    previous_bid_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='previous_bids')

    # Use a class method to get the single instance of the status
    @classmethod
    def get_instance(cls):
        # Creates the instance if it doesn't exist, otherwise returns the existing one
        return cls.objects.get_or_create(pk=1)[0]


class Settings(models.Model):
    title = models.CharField(max_length=200, default='Auction')
    auction_type = models.ForeignKey(
        'SportsType', on_delete=models.SET_NULL, null=True
    )
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    team_capacity = models.PositiveIntegerField(default=0)

    @classmethod
    def get_instance(cls):
        return cls.objects.get_or_create(pk=1)[0]


class SportsType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
