import graphene
from ogame.types import DynamicScalar, CompressedDict
from ogame.models import Player


class ScoreType(graphene.ObjectType):
    timestamp = graphene.Int()
    datetime = graphene.DateTime()
    total = DynamicScalar()
    economy = DynamicScalar()
    research = DynamicScalar()
    military = DynamicScalar()
    military_built = DynamicScalar()
    military_destroyed = DynamicScalar()
    military_lost = DynamicScalar()
    honor = DynamicScalar()

    def resolve_total(self, info, **kwargs):
        return CompressedDict.decompress_bytes(self.total)

    def resolve_economy(self, info, **kwargs):
        return CompressedDict.decompress_bytes(self.economy)

    def resolve_research(self, info, **kwargs):
        return CompressedDict.decompress_bytes(self.research)

    def resolve_military(self, info, **kwargs):
        return CompressedDict.decompress_bytes(self.military)

    def resolve_military_built(self, info, **kwargs):
        return CompressedDict.decompress_bytes(self.military_built)

    def resolve_military_destroyed(self, info, **kwargs):
        return CompressedDict.decompress_bytes(self.military_destroyed)

    def resolve_military_lost(self, info, **kwargs):
        return CompressedDict.decompress_bytes(self.military_lost)

    def resolve_honor(self, info, **kwargs):
        return CompressedDict.decompress_bytes(self.honor)


class PlayerType(graphene.ObjectType):
    player_id = graphene.Int()
    server_id = graphene.String()
    name = graphene.String()
    planets = DynamicScalar()
    scores = graphene.List(ScoreType)

    def resolve_planets(self, info, **kwargs):
        return CompressedDict.decompress_bytes(self.planets)

    def resolve_scores(self, info, **kwargs):
        return self.score_set.all()


class Query(graphene.ObjectType):
    players = graphene.List(
        PlayerType,
        name__icontains=graphene.String(
            description='Filter by player full or partial name.'
        ),
        player_id=graphene.Int(
            description='Filter by player ingame ID.'
        ),
        score__datetime__lte=graphene.DateTime(
            description='Filter players by score collected on lesser or equal inputed datetime.'
        ),
        score__datetime__gte=graphene.DateTime(
            description='Filter players by score collected on greater or equal inputed datetime.'
        )
    )

    def resolve_players(self, info, **kwargs):
        return Player.objects.filter(**kwargs)