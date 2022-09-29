from datetime import timedelta, datetime
import pytz
import graphene
from ogame.types import DynamicScalar, CompressedDict
from ogame.models import Player, Alliance
from ogame.util import get_diff_df, get_prediction_df
from ogame.forecast import predict_player_future_score


class ScorePrediction(graphene.ObjectType):
    sample_scores = graphene.List(graphene.Float)
    sample_dates = graphene.List(graphene.String)
    future_dates = graphene.List(graphene.String)
    score_predictions = graphene.List(graphene.Float)


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
    planets = DynamicScalar()
    scores = graphene.List(ScoreType)
    alliance = graphene.Field('ogame.schema.AllianceType')
    alliances_founded = graphene.List('ogame.schema.AllianceType')
    score_diff = graphene.List(ScoreDiffType)
    weekday_mean_activity = graphene.Field(WeekdayMeanActivity)
    hour_mean_activity = graphene.Field(HourMeanActivity)
    halfhour_mean_activity = graphene.Field(HourMeanActivity)
    score_prediction = graphene.Field(ScorePrediction)

    def resolve_scores(self, info, **kwargs):
        if 'scores' in self.__dict__:
            return self.scores
        return self.score_set.all()

    def resolve_score_prediction(self, info, **kwargs):
        past_datetime_limit = datetime.now() - timedelta(days=14)
        scores = self.score_set.filter(datetime__gte=past_datetime_limit)
        df, future_dates = get_prediction_df(scores)
        prediction = predict_player_future_score(df, future_dates)
        return ScorePrediction(*[
            df.total.values,
            df.index,
            prediction.index,
            prediction.values
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
        return CompressedDict.decompress_bytes(self.planets)

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
        datetime__gte=graphene.DateTime(
            description='Filter player score collected on greater or equal inputed datetime.'
        )
    )

    def resolve_players(self, info, **kwargs):
        dt_start = kwargs.pop('datetime__gte', None)
        players = Player.objects.filter(**kwargs)

        if dt_start is None:
            return players

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