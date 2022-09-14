from statistics import mode
from django.db import models


class Player(models.Model):
    player_id = models.IntegerField()
    name = models.CharField(max_length=100)
    server_id = models.CharField(max_length=10)
    positions = models.BinaryField()
    planets = models.BinaryField()
