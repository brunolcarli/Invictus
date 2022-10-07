from django.db import models


class Player(models.Model):
    player_id = models.IntegerField()
    name = models.CharField(max_length=100)
    server_id = models.CharField(max_length=10)
    planets = models.BinaryField()
    status = models.CharField(max_length=4, null=True)
    rank = models.IntegerField(null=True)
    alliance = models.ForeignKey(
        'ogame.Alliance',
        on_delete=models.CASCADE,
        null=True,
        related_name='current_alliance'
    )


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


class Alliance(models.Model):
    ally_id = models.IntegerField()
    name = models.CharField(max_length=100, null=True)
    tag = models.CharField(max_length=15, null=True)
    founder = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        null=True,
        related_name='founder_player'
    )
    found_date = models.DateTimeField(null=True)
    logo = models.TextField(null=True)
    homepage = models.TextField(null=True)
    application_open = models.BooleanField(null=True)
    members = models.ManyToManyField(Player, related_name='ally_members')
    planets_distribution_coords = models.BinaryField(null=True)
    planets_distribution_by_galaxy = models.BinaryField(null=True)


class PastScorePrediction(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    date = models.DateField(null=True)
    prediction = models.BinaryField(null=True)


class CombatReport(models.Model):
    url = models.TextField()
    title = models.TextField()
    date = models.DateField(null=True)
    winner = models.CharField(max_length=50, null=True, blank=True)
    attackers = models.BinaryField(null=True)
    defenders = models.BinaryField(null=True)


# class ActivityPredictionHistory(models.Model):
#     player = models.ForeignKey(Player, on_delete=models.CASCADE)
#     start_date = models.DateField(null=True)
#     end_date = models.DateField(null=True)
#     predicted = models.BinaryField(null=True)
#     groundtruth = models.BinaryField(null=True)

