from time import sleep
from datetime import datetime
import ogame_stats
from ogame.models import Player, Score
from ogame.types import CompressedDict


class OgameStatsCrawler:
    SERVER_ID = 144
    COMMUNITY = 'br'

    @staticmethod
    def get_universe_data():
        data = ogame_stats.UniverseQuestions(
            OgameStatsCrawler.SERVER_ID,
            OgameStatsCrawler.COMMUNITY
        )
        return data

    @staticmethod
    def update_player_data(data):
        player, _ = Player.objects.get_or_create(
            player_id=int(data['id']),
            server_id=data['serverId']
        )

        player.name = data['name']
        print(f'Updating player: {player.player_id}:{player.name}')
        player.planets = CompressedDict(data['planets']).bit_string
        player.save()

        score, created = Score.objects.get_or_create(
            player=player,
            timestamp=int(data['timestamp'])    
        )

        if not created:
            return

        print(f'Updating score for player: {player.player_id}:{player.name}')
        scores = {}
        switch = {
            '0': 'total',
            '1': 'economy',
            '2': 'research',
            '3': 'military',
            '4': 'military_built',
            '5': 'military_destroyed',
            '6': 'military_lost',
            '7': 'honor'
        }
        for position in data['positions']['position']:
            if int(position['type']) > 7:
                continue

            score_type = position['type']
            if score_type == '3':
                scores[switch[score_type]] = CompressedDict({
                    'score': float(position['score']),
                    'rank': int(position['#text']),
                    'ships': int(position['ships'])
                }).bit_string

            else:
                scores[switch[score_type]] = CompressedDict({
                    'score': float(position['score']),
                    'rank': int(position['#text'])
                }).bit_string

        score.total = scores['total']
        score.economy = scores['economy']
        score.research = scores['research']
        score.military = scores['military']
        score.military_built = scores['military_built']
        score.military_destroyed = scores['military_destroyed']
        score.military_lost = scores['military_lost']
        score.honor = scores['honor']
        score.datetime = datetime.fromtimestamp(score.timestamp)
        score.save()

    @staticmethod
    def crawl():
        while True:
            universe = OgameStatsCrawler.get_universe_data()
            for player in universe.players.name.values:
                try:
                    data = universe.get_player_data(player)
                    OgameStatsCrawler.update_player_data(data['playerData'])
                except:
                    continue
            sleep(3600*12)
