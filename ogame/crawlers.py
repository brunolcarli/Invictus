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
    def get_highscore_data():
        data = ogame_stats.HighScoreQuestions(
            OgameStatsCrawler.SERVER_ID,
            OgameStatsCrawler.COMMUNITY
        )
        return data

    @staticmethod
    def update_player_data(data, player_id, highscores):
        player, _ = Player.objects.get_or_create(
            player_id=int(player_id),
            server_id=data['serverId']
        )

        player.name = data['name']
        print(f'Updating player: {player.player_id}:{player.name}')
        player.planets = CompressedDict(data['planets']).bit_string
        player.save()

        dt_reference = datetime.utcnow()
        score, created = Score.objects.get_or_create(
            player=player,
            timestamp=dt_reference.timestamp()
        )

        if not created:
            return

        print(f'Updating score for player: {player.player_id}:{player.name}')
        player_id = str(player_id)
        try:
            total = highscores.total[['position', 'score']].loc[highscores.total.id == player_id].values[0]
            economy = highscores.economy[['position', 'score']].loc[highscores.economy.id == player_id].values[0]
            research = highscores.research[['position', 'score']].loc[highscores.research.id == player_id].values[0]
            military = highscores.military[['position', 'score', 'ships']].loc[highscores.military.id == player_id].values[0]
            military_built = highscores.military_built[['position', 'score']].loc[highscores.military_built.id == player_id].values[0]
            military_destroyed = highscores.military_destroyed[['position', 'score']].loc[highscores.military_destroyed.id == player_id].values[0]
            military_lost = highscores.military_lost[['position', 'score']].loc[highscores.military_lost.id == player_id].values[0]
            honor = highscores.honor[['position', 'score']].loc[highscores.honor.id == player_id].values[0]
        except IndexError:
            print(f'Failed retrieving {player.name} score')
            return

        score.total = CompressedDict({
            'score': float(total[0]),
            'rank': int(total[1])}
        ).bit_string
        score.economy = CompressedDict({
            'score': float(economy[0]),
            'rank': int(economy[1])}
        ).bit_string
        score.research = CompressedDict({
            'score': float(research[0]),
            'rank': int(research[1])}
        ).bit_string
        score.military = CompressedDict({
            'score': float(military[0]),
            'rank': int(military[1]),
            'ships': int(military[2])
        }).bit_string
        score.military_built = CompressedDict({
            'score': float(military_built[0]),
            'rank': int(military_built[1])}
        ).bit_string
        score.military_destroyed = CompressedDict({
            'score': float(military_destroyed[0]),
            'rank': int(military_destroyed[1])}
        ).bit_string
        score.military_lost = CompressedDict({
            'score': float(military_lost[0]),
            'rank': int(military_lost[1])}
        ).bit_string
        score.honor = CompressedDict({
            'score': float(honor[0]),
            'rank': int(honor[1])}
        ).bit_string
        score.datetime = dt_reference
        score.save()

    @staticmethod
    def crawl():
        while True:
            universe = OgameStatsCrawler.get_universe_data()
            highscores = OgameStatsCrawler.get_highscore_data()
            for player_id, player_name in universe.players[['id', 'name']].values:
                try:
                    data = universe.get_player_data(player_name)
                    OgameStatsCrawler.update_player_data(data['playerData'], player_id, highscores)
                except:
                    continue
            sleep(3600*2)
