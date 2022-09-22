from django.db import models


class Player(models.Model):
    player_id = models.IntegerField()
    name = models.CharField(max_length=100)
    server_id = models.CharField(max_length=10)
    planets = models.BinaryField()
    status = models.CharField(max_length=4, null=True)


class Score(models.Model):
    timestamp = models.IntegerField()
    datetime = models.DateTimeField(null=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    total = models.BinaryField()
    economy = models.BinaryField()
    research = models.BinaryField()
    military = models.BinaryField()
    military_built = models.BinaryField()
    military_destroyed = models.BinaryField()
    military_lost = models.BinaryField()
    honor = models.BinaryField()
