from collections import OrderedDict
from ast import literal_eval
from datetime import timedelta, datetime
import pytz
import graphene
from ogame.types import DynamicScalar, CompressedDict
from ogame.models import Player, Alliance, PastScorePrediction, Score, CombatReport
from ogame.util import get_prediction_df, get_future_activity
from ogame.forecast import predict_player_future_score
from ogame.statistics import (weekday_relative_freq, hour_relative_freq,
                              fleet_relative_freq, universe_fleet_relative_freq)


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


class HourRelativeFrequency(graphene.ObjectType):
    hours = graphene.List(graphene.String)
    relative_frequency = graphene.List(graphene.Float)
    high_std = graphene.List(graphene.Float)
    low_std = graphene.List(graphene.Float)


class WeekdayRelativeFrequency(graphene.ObjectType):
    weekdays = graphene.List(graphene.String)
    relative_frequency = graphene.List(graphene.Float)
    high_std = graphene.List(graphene.Float)
    low_std = graphene.List(graphene.Float)


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
    score_prediction = graphene.Field(ScorePrediction)
    activity_prediction = DynamicScalar()
    planets_count = graphene.Int()
    rank = graphene.Int()
    ships_count = graphene.Int()
    combat_reports_count = graphene.Int()
    combat_reports = graphene.List('ogame.schema.CombatReportType')
    weekday_relative_frequency = graphene.Field(WeekdayRelativeFrequency)
    halfhour_relative_frequency = graphene.Field(HourRelativeFrequency)
    hour_relative_frequency = graphene.Field(HourRelativeFrequency)
    fleet_relative_frequency = DynamicScalar()

    def resolve_fleet_relative_frequency(self, info, **kwargs):
        return fleet_relative_freq(self).to_dict()['FREQ']

    def resolve_hour_relative_frequency(self, info, **kwargs):
        if 'scores' in self.__dict__:
            scores = self.scores
        else:
            scores = self.score_set.filter(datetime__isnull=False)
        if not scores:
            return None

        rel_freq = hour_relative_freq(scores, '3600S')
        return HourRelativeFrequency(
            hours=rel_freq.index.values,
            relative_frequency=rel_freq.REL_FREQ.values,
            high_std=rel_freq.POS_STD.values,
            low_std=rel_freq.NEG_STD.values
        )

    def resolve_halfhour_relative_frequency(self, info, **kwargs):
        if 'scores' in self.__dict__:
            scores = self.scores
        else:
            scores = self.score_set.filter(datetime__isnull=False)
        if not scores:
            return None

        rel_freq = hour_relative_freq(scores, '1800S')
        return HourRelativeFrequency(
            hours=rel_freq.index.values,
            relative_frequency=rel_freq.REL_FREQ.values,
            high_std=rel_freq.POS_STD.values,
            low_std=rel_freq.NEG_STD.values
        )

    def resolve_weekday_relative_frequency(self, info, **kwargs):
        if 'scores' in self.__dict__:
            scores = self.scores
        else:
            scores = self.score_set.filter(datetime__isnull=False)
        if not scores:
            return None

        rel_freq = weekday_relative_freq(scores)
        return WeekdayRelativeFrequency(
            weekdays=rel_freq.index.values,
            relative_frequency=rel_freq.REL_FREQ.values,
            high_std=rel_freq.POS_STD.values,
            low_std=rel_freq.NEG_STD.values
        )

    def resolve_combat_reports_count(self, info, **kwargs):
        return self.combat_report_attacker.count() + self.combat_report_defender.count()

    def resolve_combat_reports(self, info, **kwargs):
        return (self.combat_report_attacker.all() | self.combat_report_defender.all()).distinct()

    def resolve_ships_count(self, info, **kwargs):
        return CompressedDict.decompress_bytes(self.score_set.last().military).get('ships', 0)

    def resolve_activity_prediction(self, info, **kwargs):
        if 'scores' in self.__dict__:
            scores = self.scores
        else:
            scores = self.score_set.filter(datetime__isnull=False)
        if not scores:
            return None

        preds = get_future_activity(scores)
        return OrderedDict({i: list(preds[i].values) for i in preds.columns})

    def resolve_planets_count(self, info, **kwargs):
        planets = CompressedDict.decompress_bytes(self.planets).get('planet', [])
        if isinstance(planets, dict):
            return 1
        return len(planets)

    def resolve_scores(self, info, **kwargs):
        if 'scores' in self.__dict__:
            return self.scores
        return self.score_set.filter(datetime__isnull=False)

    def resolve_score_prediction(self, info, **kwargs):
        today = datetime.now()
        past_datetime_limit = today - timedelta(days=14)
        scores = self.score_set.filter(
            datetime__gte=past_datetime_limit,
            datetime__isnull=False
        )
        if not scores:
            return

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
        elif (today.date() - last_prediction.date).days > 2:
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

    def resolve_alliances_founded(self, info, **kwargs):
        return Alliance.objects.filter(founder__player_id=self.player_id)

    def resolve_planets(self, info, **kwargs):
        data = CompressedDict.decompress_bytes(self.planets).get('planet', [])
        if not data:
            return None
        if isinstance(data, dict):
            coords = data['coords'].split(':')
            coords.append(data['name'])
            return [PlanetType(*coords)]
        planets = []
        for planet in data:
            coords = planet['coords'].split(':')
            coords.append(planet['name'])
            planets.append(coords)

        return [PlanetType(*planet) for planet in planets]


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
    fleet_relative_frequency = DynamicScalar()

    def resolve_fleet_relative_frequency(self, info, **kwargs):
        members = self.members.all()
        if not members.exists():
            return {}
        df = fleet_relative_freq(members[0])
        if members.count() < 2:
            return df.to_dict()['FREQ']

        count = 1 if df['FREQ'].sum() > 0 else 0

        for member in members[1:]:
            member_freq = fleet_relative_freq(member)
            if member_freq['FREQ'].sum() > 0:
                count += 1
                df['FREQ'] += member_freq['FREQ']

        df['FREQ'] = df['FREQ'] / count
        return df.round(2).to_dict()['FREQ']

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


class CombatReportType(graphene.ObjectType):
    title = graphene.String()
    url = graphene.String()
    winner = graphene.String()
    date = graphene.Date()
    attackers_fleet = DynamicScalar()
    defenders_fleet = DynamicScalar()
    attacker_players = graphene.List(PlayerType)
    defender_players = graphene.List(PlayerType)

    def resolve_attacker_players(self, info, **kwargs):
        return self.attacker_players.all()

    def resolve_defender_players(self, info, **kwargs):
        return self.defender_players.all()

    def resolve_attackers_fleet(self, info, **kwargs):
        return CompressedDict.decompress_bytes(self.attackers)

    def resolve_defenders_fleet(self, info, **kwargs):
        return CompressedDict.decompress_bytes(self.defenders)


############################################
#
#                 QUERY
#
############################################
class Query(graphene.ObjectType):
    player = graphene.Field(
        PlayerType,
        name__icontains=graphene.String(
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
        if not kwargs:
            raise Exception('Player name or player ID is required for this filter')

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
                datetime__gte=dt_start.astimezone(pytz.timezone('UTC')),
                datetime__isnull=False
            )
            return player
        
        if dt_start is None and dt_stop:
            player.scores = player.score_set.filter(
                datetime__lte=dt_stop.astimezone(pytz.timezone('UTC')),
                datetime__isnull=False
            )
            return player

        player.scores = player.score_set.filter(
            datetime__gte=dt_start.astimezone(pytz.timezone('UTC')),
            datetime__lte=dt_stop.astimezone(pytz.timezone('UTC')),
            datetime__isnull=False
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
            return players.order_by('rank')

        for player in players:
            player.scores = player.score_set.filter(
                datetime__gte=dt_start.astimezone(pytz.timezone('UTC')),
                datetime__isnull=False
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
        kwargs['datetime__isnull'] = False
        return Score.objects.filter(**kwargs)

    combat_reports = graphene.List(
        CombatReportType,
        attacker_players__name__in=graphene.List(
            graphene.String,
            description='Filter reports by attackers player name'
        ),
        defender_players__name__in=graphene.List(
            graphene.String,
            description='Filter reports by defenders player name'
        ),
        title__icontains=graphene.String(
            description='Filter reports by partial title content'
        ),
        date__gte=graphene.Date(
            description='Filter reports from dates greater or equal inputed date'
        ),
        date__lte=graphene.Date(
            description='Filter reports from dates lesser or equal inputed date'
        ),
        winner=graphene.String(
            description='Filter reports by win result: [attackers, defenders, draw]'
        )
    )

    def resolve_combat_reports(self, info, **kwargs):
        return CombatReport.objects.filter(**kwargs)

    combat_report = graphene.Field(
        CombatReportType,
        attacker_players__name__in=graphene.List(
            graphene.String,
            description='Filter reports by attackers player name'
        ),
        defender_players__name__in=graphene.List(
            graphene.String,
            description='Filter reports by defenders player name'
        ),
        title__icontains=graphene.String(
            required=True,
            description='Filter reports by partial title content'
        ),
        date__gte=graphene.Date(
            description='Filter reports from dates greater or equal inputed date'
        ),
        date__lte=graphene.Date(
            description='Filter reports from dates lesser or equal inputed date'
        ),
        winner=graphene.String(
            description='Filter reports by win result: [attackers, defenders, draw]'
        )
    )

    def resolve_combat_report(self, info, **kwargs):
        return CombatReport.objects.get(**kwargs)

    universe_fleet_relative_frequency = DynamicScalar()

    def resolve_universe_fleet_relative_frequency(self, info, **kwargs):
        return universe_fleet_relative_freq(CombatReport.objects.all()).to_dict()['FREQ']
