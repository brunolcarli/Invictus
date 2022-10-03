from ast import literal_eval
from datetime import timedelta, datetime
import pytz
import graphene
from ogame.types import DynamicScalar, CompressedDict
from ogame.models import Player, Alliance, PastScorePrediction, Score
from ogame.util import get_diff_df, get_prediction_df
from ogame.forecast import predict_player_future_score


class PlanetType(graphene.ObjectType):
    galaxy = graphene.Int()
    solar_system = graphene.Int()
    position = graphene.Int()
    name = graphene.String()
    raw_coord = graphene.String()

    def resolve_raw_coord(self, info, **kwargs):
        return f'{self.galaxy}:{self.solar_system}:{self.position}'


class LastScorePredictionType(graphene.ObjectType):
    dates = graphene.List(graphene.String)
    predictions = graphene.List(graphene.Float)


class ScorePrediction(graphene.ObjectType):
    sample_scores = graphene.List(graphene.Float)
    sample_dates = graphene.List(graphene.String)
    future_dates = graphene.List(graphene.String)
    score_predictions = graphene.List(graphene.Float)
    last_predictions = graphene.Field(LastScorePredictionType)


class HourMeanActivity(graphene.ObjectType):
    hours = graphene.List(graphene.String)
    average_progress = graphene.List(graphene.Float)


class WeekdayMeanActivity(graphene.ObjectType):
    weekdays = graphene.List(graphene.String)
    average_progress = graphene.List(graphene.Float)


class ScoreDiffType(graphene.ObjectType):
    datetime = graphene.DateTime()
    total = graphene.Float()
    economy = graphene.Float()
    research = graphene.Float()
    military = graphene.Float()
    ships = graphene.Float()
    military_built = graphene.Float()
    military_destroyed = graphene.Float()
    military_lost = graphene.Float()
    honor = graphene.Float()

    def resolve_datetime(self, info, **kwargs):
        try:
            return self.datetime.astimezone(pytz.timezone('America/Sao_Paulo'))
        except Exception as err:
            print(f'FieldResolverError: Failed to resolve field with error: {str(err)}')


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

    def resolve_datetime(self, info, **kwargs):
        try:
            return self.datetime.astimezone(pytz.timezone('America/Sao_Paulo'))
        except Exception as err:
            print(f'FieldResolverError: Failed to resolve field with error: {str(err)}')

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
    status = graphene.String()
    planets = graphene.List(PlanetType)
    scores = graphene.List(ScoreType)
    alliance = graphene.Field('ogame.schema.AllianceType')
    alliances_founded = graphene.List('ogame.schema.AllianceType')
    score_diff = graphene.List(ScoreDiffType)
    weekday_mean_activity = graphene.Field(WeekdayMeanActivity)
    hour_mean_activity = graphene.Field(HourMeanActivity)
    halfhour_mean_activity = graphene.Field(HourMeanActivity)
    score_prediction = graphene.Field(ScorePrediction)
    planets_count = graphene.Int()
    rank = graphene.Int()

    def resolve_planets_count(self, info, **kwargs):
        return len(CompressedDict.decompress_bytes(self.planets).get('planet', []))

    def resolve_scores(self, info, **kwargs):
        if 'scores' in self.__dict__:
            return self.scores
        return self.score_set.all()

    def resolve_score_prediction(self, info, **kwargs):
        today = datetime.now()
        past_datetime_limit = today - timedelta(days=14)
        scores = self.score_set.filter(datetime__gte=past_datetime_limit)
        df, future_dates = get_prediction_df(scores)
        prediction = predict_player_future_score(df, future_dates)

        last_prediction, _ = PastScorePrediction.objects.get_or_create(player=self)
        if last_prediction.date is None:
            last_prediction.date = today.date()
            last_prediction.prediction = CompressedDict({
                'dates': list(prediction.index.date.astype(str)),
                'predictions': list(prediction.values)
            }).bit_string
            last_prediction.save()
        elif (today.date() - last_prediction.date).days > 14:
            last_prediction.date = today.date()
            last_prediction.prediction = CompressedDict({
                'dates': list(prediction.index.date.astype(str)),
                'predictions': list(prediction.values)
            }).bit_string
            last_prediction.save()

        return ScorePrediction(*[
            df.total.values,
            df.index.date,
            prediction.index.date,
            prediction.values,
            CompressedDict.decompress_bytes(last_prediction.prediction)
        ])

    def resolve_halfhour_mean_activity(self, info, **kwargs):
        if 'scores' in self.__dict__:
            dataframe = get_diff_df(self.scores)
        else:
            dataframe = get_diff_df(self.score_set.all())

        dataframe = dataframe.set_index(dataframe.datetime)
        dataframe['halfhour'] = dataframe.index.round(freq='1800S').strftime('%H:'+'%M')
        dataframe = dataframe[['total', 'halfhour']].groupby('halfhour').mean().fillna(0)
        return HourMeanActivity(*[dataframe.index.values, dataframe.total.values])
    
    def resolve_hour_mean_activity(self, info, **kwargs):
        if 'scores' in self.__dict__:
            dataframe = get_diff_df(self.scores)
        else:
            dataframe = get_diff_df(self.score_set.all())

        dataframe = dataframe.set_index(dataframe.datetime)
        dataframe['hour'] = dataframe.index.round(freq='3600S').strftime('%H:'+'%M')
        dataframe = dataframe[['total', 'hour']].groupby('hour').mean().fillna(0)
        return HourMeanActivity(*[dataframe.index.values, dataframe.total.values])

    def resolve_weekday_mean_activity(self, info, **kwargs):
        if 'scores' in self.__dict__:
            dataframe = get_diff_df(self.scores)
        else:
            dataframe = get_diff_df(self.score_set.all())

        dataframe = dataframe.set_index(dataframe.datetime)
        dataframe['weekday'] = dataframe.index.strftime('%A')
        dataframe = dataframe[['total', 'weekday']].groupby('weekday').mean().fillna(0)
        return WeekdayMeanActivity(*[dataframe.index.values, dataframe.total.values])

    def resolve_alliances_founded(self, info, **kwargs):
        return Alliance.objects.filter(founder__player_id=self.player_id)

    def resolve_planets(self, info, **kwargs):
        data = CompressedDict.decompress_bytes(self.planets).get('planet', [])
        if not isinstance(data, list):
            return None
        planets = []
        for planet in data:
            coords = planet['coords'].split(':')
            coords.append(planet['name'])
            planets.append(coords)

        return [PlanetType(*planet) for planet in planets]

    def resolve_score_diff(self, info, **kwargs):
        if 'scores' in self.__dict__:
            dataframe = get_diff_df(self.scores)
        else:
            dataframe = get_diff_df(self.score_set.all())

        return [ScoreDiffType(*row) for row in dataframe.values[1:]]


class AllianceType(graphene.ObjectType):
    ally_id = graphene.Int()
    name = graphene.String()
    tag = graphene.String()
    founder = graphene.Field(PlayerType)
    found_date = graphene.DateTime()
    logo = graphene.String()
    homepage = graphene.String()
    application_open = graphene.Boolean()
    members = graphene.List(PlayerType)
    planets_distribution_coords = graphene.List(PlanetType)
    planets_distribution_by_galaxy = DynamicScalar()
    players_count = graphene.Int()
    planets_count = graphene.Int()
    ships_count = graphene.Int()

    def resolve_ships_count(self, info, **kwargs):
        members = self.members.all()
        ships = [CompressedDict.decompress_bytes(member.score_set.last().military).get('ships', 0)
                 for member in members]
        return sum(ships)

    def resolve_players_count(self, info, **kwargs):
        return self.members.count()

    def resolve_planets_count(self, info, **kwargs):
        try:
            planets = literal_eval(self.planets_distribution_coords.decode('utf-8'))
        except:
            return 0
        return len(planets)

    def resolve_members(self, info, **kwargs):
        return self.members.all()

    def resolve_planets_distribution_coords(self, info, **kwargs):
        try:
            planets = literal_eval(self.planets_distribution_coords.decode('utf-8'))
        except:
            return None
        return [PlanetType(*planet.split(':')) for planet in planets]

    def resolve_planets_distribution_by_galaxy(self, info, **kwargs):
        return CompressedDict.decompress_bytes(self.planets_distribution_by_galaxy)

    def resolve_found_date(self, info, **kwargs):
        try:
            return self.datetime.astimezone(pytz.timezone('America/Sao_Paulo'))
        except Exception as err:
            print(f'FieldResolverError: Failed to resolve field with error: {str(err)}')


class Query(graphene.ObjectType):
    player = graphene.Field(
        PlayerType,
        name__icontains=graphene.String(
            required=True,
            description='Filter by player full or partial name.'
        ),
        status=graphene.String(
            description='Filter by player status.'
        ),
        player_id=graphene.Int(
            description='Filter by player ingame ID.'
        ),
        datetime__lte=graphene.DateTime(
            description='Filter player score collected on lesser or equal inputed datetime.'
        ),
        datetime__gte=graphene.DateTime(
            description='Filter player score collected on greater or equal inputed datetime.'
        )
    )
    def resolve_player(self, info, **kwargs):
        dt_start = kwargs.pop('datetime__gte', None)
        dt_stop = kwargs.pop('datetime__lte', None)
        try:
            player = Player.objects.get(**kwargs)
        except Player.DoesNotExist:
            raise Exception('Player not found')
        
        if dt_start is None and dt_stop is None:
            return player

        if dt_start and dt_stop is None:
            player.scores = player.score_set.filter(
                datetime__gte=dt_start.astimezone(pytz.timezone('UTC'))
            )
            return player
        
        if dt_start is None and dt_stop:
            player.scores = player.score_set.filter(
                datetime__lte=dt_stop.astimezone(pytz.timezone('UTC'))
            )
            return player

        player.scores = player.score_set.filter(
            datetime__gte=dt_start.astimezone(pytz.timezone('UTC')),
            datetime__lte=dt_stop.astimezone(pytz.timezone('UTC'))
        )
        return player

    players = graphene.List(
        PlayerType,
        name__in=graphene.List(
            graphene.String,
            description='Filter by players full name.'
        ),
        status=graphene.String(
            description='Filter by player status.'
        ),
        status__in=graphene.List(
            graphene.String,
            description='Filter players by possible status'
        ),
        rank__gte=graphene.Int(
            description='Filter player by rank greather equal value'
        ),
        rank__lte=graphene.Int(
            description='Filter player by rank lesser equal value'
        ),
        datetime__gte=graphene.DateTime(
            description='Filter player score collected on greater or equal inputed datetime.'
        )
    )

    def resolve_players(self, info, **kwargs):
        dt_start = kwargs.pop('datetime__gte', None)
        players = Player.objects.filter(**kwargs)

        if dt_start is None:
            return players.order_by('rank').values()

        for player in players:
            player.scores = player.score_set.filter(
                datetime__gte=dt_start.astimezone(pytz.timezone('UTC'))
            )

        return players

    alliances = graphene.List(
        AllianceType,
        name__icontains=graphene.String(),
        ally_id=graphene.Int()
    )

    def resolve_alliances(self, info, **kwargs):
        return Alliance.objects.filter(**kwargs)

    alliance = graphene.Field(
        AllianceType,
        name__icontains=graphene.String(required=True),
        ally_id=graphene.Int()
    )

    def resolve_alliance(self, info, **kwargs):
        return Alliance.objects.get(**kwargs)


    scores = graphene.List(ScoreType)

    def resolve_scores(self, info, **kwargs):
        return Score.objects.filter(**kwargs)
