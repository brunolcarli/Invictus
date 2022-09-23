from time import sleep
from datetime import datetime
import warnings
import ogame_stats
from ogame.models import Player, Score, Alliance
from ogame.types import CompressedDict


warnings.filterwarnings('ignore')


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
    def update_player_data(data, player_id, highscores, status, alliances):
        player, _ = Player.objects.get_or_create(
            player_id=int(player_id),
            server_id=data['serverId']
        )

        player.name = data['name']
        print(f'Updating player: {player.player_id}:{player.name}')
        player.status = status
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
            'score': float(total[1]),
            'rank': int(total[0])}
        ).bit_string
        score.economy = CompressedDict({
            'score': float(economy[1]),
            'rank': int(economy[0])}
        ).bit_string
        score.research = CompressedDict({
            'score': float(research[1]),
            'rank': int(research[0])}
        ).bit_string
        score.military = CompressedDict({
            'score': float(military[1]),
            'rank': int(military[0]),
            'ships': int(military[2])
        }).bit_string
        score.military_built = CompressedDict({
            'score': float(military_built[1]),
            'rank': int(military_built[0])}
        ).bit_string
        score.military_destroyed = CompressedDict({
            'score': float(military_destroyed[1]),
            'rank': int(military_destroyed[0])}
        ).bit_string
        score.military_lost = CompressedDict({
            'score': float(military_lost[1]),
            'rank': int(military_lost[0])}
        ).bit_string
        score.honor = CompressedDict({
            'score': float(honor[1]),
            'rank': int(honor[0])}
        ).bit_string
        score.datetime = dt_reference
        score.save()

        if not data.get('alliance'):
            return

        ally_data = alliances.loc[alliances.id == data['alliance'].get('id')]
        if len(ally_data.values) < 1:
            return

        print(f'Updating alliance for player: {player.player_id}:{player.name}')
        try:
            ally, created = Alliance.objects.get_or_create(ally_id=int(data['alliance']['id']))
        except Exception as err:
            print('Ally update error: ', str(err))

        # first row if exists
        ally_data = ally_data.values[0]
        _, name, tag, founder, found_date, is_open, logo, homepage = ally_data

        if player.player_id != int(founder):
            try:
                founder = Player.objects.get(player_id=int(founder))
            except Player.DoesNotExist:
                founder = None
        else:
            founder = player

        is_open = None if not str(is_open.isdigit()) else bool(int(is_open))

        ally.name = name
        ally.tag = tag
        ally.founder = founder
        ally.found_date = datetime.fromtimestamp(int(found_date))
        ally.application_open = bool(int(is_open))
        ally.logo = logo
        ally.homepage = homepage
        ally.save()

        player.alliance = ally
        player.save()
        print('Done!')

    @staticmethod
    def crawl():
        while True:
            universe = OgameStatsCrawler.get_universe_data()
            alliances = universe.alliances
            highscores = OgameStatsCrawler.get_highscore_data()
            for player_id, player_name, status in universe.players[['id', 'name', 'status']].values:
                try:
                    data = universe.get_player_data(player_name)
                    OgameStatsCrawler.update_player_data(
                        data['playerData'],
                        player_id,
                        highscores,
                        status,
                        alliances
                    )
                except:
                    print(f'Crawling Error: Failed updating player {player_name}')
                    continue
            sleep(3600*2)
