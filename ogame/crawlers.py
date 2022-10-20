import re
import requests
from bs4 import BeautifulSoup
from dateutil import parser
from time import sleep
from datetime import datetime
import warnings
import ogame_stats
from ogame.models import Player, Score, Alliance, CombatReport
from ogame.types import CompressedDict


warnings.filterwarnings('ignore')


class OgameStatsCrawler:
    """
    Scaps data from Ogame API.
    """
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
        # print(f'Updating player: {player.player_id}:{player.name}')
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

        # print(f'Updating score for player: {player.player_id}:{player.name}')
        player_id = str(player_id)
        try:
            total = highscores.total[['position', 'score']].loc[highscores.total.id == player_id].fillna(0).values[0]
            economy = highscores.economy[['position', 'score']].loc[highscores.economy.id == player_id].fillna(0).values[0]
            research = highscores.research[['position', 'score']].loc[highscores.research.id == player_id].fillna(0).values[0]
            military = highscores.military[['position', 'score', 'ships']].loc[highscores.military.id == player_id].fillna(0).values[0]
            military_built = highscores.military_built[['position', 'score']].loc[highscores.military_built.id == player_id].fillna(0).values[0]
            military_destroyed = highscores.military_destroyed[['position', 'score']].loc[highscores.military_destroyed.id == player_id].fillna(0).values[0]
            military_lost = highscores.military_lost[['position', 'score']].loc[highscores.military_lost.id == player_id].fillna(0).values[0]
            honor = highscores.honor[['position', 'score']].loc[highscores.honor.id == player_id].fillna(0).values[0]
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
        player.rank = int(total[0])
        player.save()

        if not data.get('alliance'):
            player.alliance = None
            player.save()
            return

        ally_data = alliances.loc[alliances.id == data['alliance'].get('id')]
        if len(ally_data.values) < 1:
            return

        # print(f'Updating alliance for player: {player.player_id}:{player.name}')
        try:
            ally, created = Alliance.objects.get_or_create(ally_id=int(data['alliance']['id']))
        except Exception as err:
            print(f'Ally {data["alliance"].get("name")} update error: {str(err)} on player {player.name}')
            return

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

        is_open = None if not str(is_open).isdigit() else bool(int(is_open))

        ally.name = name
        ally.tag = tag
        ally.founder = founder
        ally.found_date = datetime.fromtimestamp(int(found_date))
        ally.application_open = is_open
        ally.logo = logo
        ally.homepage = homepage
        ally.save()

        player.alliance = ally
        player.save()

    @staticmethod
    def update_ally_data(ally, universe):
        try:
            galaxy_distribution = universe.get_planets_distribution_by_galaxy(ally.tag)
        except:
            raise Exception(f'Failed retrieving distribution data of ally: {ally.name}')

        try:
            ally_planets = universe.get_planets_of_alliance(ally.tag)
        except:
            raise Exception(f'Failed retrieving planets data of ally: {ally.name}')

        try:
            ally_members = universe.get_players_of_alliance(ally.tag).id.astype('int').values
        except:
            raise Exception(f'Failed retrieving members of ally: {ally.name}')

        # print(f'Updating alliance: {ally.name}')
        ally.planets_distribution_coords = CompressedDict(ally_planets).bit_string
        ally.planets_distribution_by_galaxy = CompressedDict(galaxy_distribution).bit_string
        
        ally.members.clear()
        ally.members.set(Player.objects.filter(player_id__in=ally_members))
        ally.save()
        # print(f'Updated alliance {ally.name} data!')

    @staticmethod
    def crawl():
        while True:
            universe = OgameStatsCrawler.get_universe_data()
            alliances = universe.alliances
            highscores = OgameStatsCrawler.get_highscore_data()
            for player_id, player_name, status in universe.players[['id', 'name', 'status']].values:
                try:
                    data = universe.get_player_data(player_name)
                except ogame_stats.utils.xmltodict.expat.ExpatError:
                    #  third party lib error, skip
                    continue

                try:
                    OgameStatsCrawler.update_player_data(
                        data['playerData'],
                        player_id,
                        highscores,
                        status,
                        alliances
                    )
                except Exception as err:
                    print(f'Crawling Error: Failed updating player {player_name} with error: {str(err)}')
                    continue
                    
            
            for alliance in Alliance.objects.all():
                try:
                    OgameStatsCrawler.update_ally_data(alliance, universe)
                except Exception as err:
                    print(f'CrawlingError: Failed updating alliance {alliance.name} with error: {str(err)}')
                    continue

            # Update deleted players status
            for player in Player.objects.all():
                if player.status == 'del':
                    continue
                try:
                    universe.get_player_data(player.name)
                except IndexError:
                    # Player was deleted
                    player.status = 'del'
                    player.save()
                except ogame_stats.utils.xmltodict.expat.ExpatError:
                    # third part lib faulure
                    continue

            sleep(3600*2)


class OgameForumCrawler:
    """
    Scraps data from Ogame Forum
    """
    # FORUM_URL = 'https://forum.pt.ogame.gameforge.com/forum/board/26-relat%C3%B3rios-de-combate/?labelIDs%5B2%5D=75'
    FORUM_URL = 'https://forum.pt.ogame.gameforge.com/forum/board/26-relat%C3%B3rios-de-combate/?pageNo=1&labelIDs%5B2%5D=75'

    @staticmethod
    def get_thread_list(url):
        response = requests.get(url).content
        main_threads_html = BeautifulSoup(response, 'html.parser')
        combat_reports = main_threads_html.findAll(class_='messageGroupLink')
        return [{'title': i.text, 'url': i.attrs.get('href')} for i in combat_reports]

    @staticmethod
    def is_defense(text):
        return bool(ForumReportText.DEFENSES_REGEX.search(text))

    @staticmethod
    def is_ship(text):
        return bool(ForumReportText.SHIPS_REGEX.search(text))

    @staticmethod
    def is_noise(text):
        return bool(ForumReportText.NOISE_REGEX.search(text))

    @staticmethod
    def get_count(text):
        tokens = text.split()
        for token in tokens:
            match = re.search('[0-9]+.+[0-9]', token)
            if bool(match):
                return int(token.replace('.', ''))

        # if no floating point number was found maybe its preented as integer
        for token in tokens:
            match = re.search('[0-9]', token)
            if bool(match):
                return int(token)

    @staticmethod
    def get_ship_from_text(text):
        eye = ForumReportText.SHIPS_REGEX.search(text)
        start, end = eye.start(), eye.end()
        return text[start:end]

    @staticmethod
    def get_defense_from_text(text):
        eye = ForumReportText.DEFENSES_REGEX.search(text)
        start, end = eye.start(), eye.end()
        return text[start:end]

    @staticmethod
    def get_report_combat_data(message_text):
        combat_data = {
            'date': None,
            'attackers': {},
            'defenders': {},
            'winner': None
        }
        cursor = None

        for text_line in message_text:
            text_line = text_line.text

            if not text_line:
                continue

            if OgameForumCrawler.is_noise(text_line):
                continue

            elif '--:--:--' in text_line:
                combat_data['date'] = str(parser.parse(text_line, fuzzy=True).date())

            elif 'Atacante' in text_line:
                attacker = text_line.split('Atacante')[-1].strip()
                cursor = ('attackers', attacker)
                if attacker not in combat_data['attackers']:
                    combat_data['attackers'][attacker] = {'ships': {}}

            elif OgameForumCrawler.is_ship(text_line):
                try:
                    subject, name = cursor
                except TypeError:
                    # maybe some text mentioned a ship, ignore and continue
                    continue

                ship = OgameForumCrawler.get_ship_from_text(text_line)
                count = OgameForumCrawler.get_count(text_line)
                if ship not in combat_data[subject][name]['ships']:
                    combat_data[subject][name]['ships'][ship] = count

            elif 'Defensor' in text_line:
                defender = text_line.split('Defensor')[-1].strip()
                cursor = ('defenders', defender)
                if defender not in combat_data['defenders']:
                    combat_data['defenders'][defender] = {'ships': {}, 'defenses': {}}

            elif OgameForumCrawler.is_defense(text_line):
                try:
                    subject, name = cursor
                except TypeError:
                    # maybe some text mentioned a defense, ignore and continue
                    continue

                defense = OgameForumCrawler.get_defense_from_text(text_line)
                count = OgameForumCrawler.get_count(text_line)
                if defense not in combat_data[subject][name]['defenses']:
                    combat_data[subject][name]['defenses'][defense] = count
                    
            elif 'venceu a batalha' in text_line:
                if 'atacante' in text_line.lower():
                    combat_data['winner'] = 'attackers'
                elif 'defensor' in text_line.lower():
                    combat_data['winner'] = 'defenders'
                return combat_data

            elif 'batalha terminou empatada' in text_line:
                combat_data['winner'] = 'draw'
                return combat_data

        return combat_data

    @staticmethod
    def crawl():
        while True:
            forum_url = OgameForumCrawler.FORUM_URL
            for page_num in range(1, 26):
                threads = OgameForumCrawler.get_thread_list(forum_url)
                for thread in threads:
                    url = thread.get('url')
                    title = thread.get('title')
                    if not url or not title:
                        print(f'Skipping save of thread {thread}')
                        continue

                    combat_report, created = CombatReport.objects.get_or_create(
                        title=title,
                        url=url
                    )
                    if not created:
                        continue

                    thread_html = BeautifulSoup(requests.get(url).content, 'html.parser')
                    message_text = thread_html.find(class_='messageText').findAll('p')
                    report_data = OgameForumCrawler.get_report_combat_data(message_text)

                    attackers = []
                    defenders = []
                    # slice player name from [ally tag]
                    for attacker in list(report_data['attackers'].keys()):
                        attackers.append(attacker.split('[')[0].strip())

                    for defender in list(report_data['defenders'].keys()):
                        defenders.append(defender.split('[')[0].strip())

                    # try to retrieve players record from database
                    attacker_players = Player.objects.filter(name__in=attackers)
                    defender_players = Player.objects.filter(name__in=defenders)

                    try:
                        combat_report.date = parser.parse(report_data['date'])
                        combat_report.winner = report_data['winner']
                        combat_report.attackers = CompressedDict(report_data['attackers']).bit_string
                        combat_report.defenders = CompressedDict(report_data['defenders']).bit_string
                        combat_report.attacker_players.set(attacker_players)
                        combat_report.defender_players.set(defender_players)
                        combat_report.save()
                    except Exception as err:
                        print(f'Failed saving report {thread.get("url")} with error {str(err)}')
                        continue
                forum_url = forum_url.replace(f'pageNo={page_num}', f'pageNo={page_num+1}')
            sleep(3600*24)


class ForumReportText:
    """
    Filter tool to some common words on forum combat reports.
    """
    SHIPS = (
        'Caça Ligeiro', 'Light Fighter',
        'Caça Pesado', 'Heavy Fighter',
        'Cruzador', 'Cruiser',
        'Nave de Batalha', 'Battleship',
        'Interceptador', 'Interceptor', 'Battlecruiser',
        'Destruidor', 'Destroyer',
        'Bombardeiro', 'Bomber',
        'Estrela da Morte', 'Deathstar', 'Death Star', 'EDM',
        'Ceifeira', 'Reaper',
        'Explorador', 'Pathfinder',
        'Cargueiro Pequeno', 'Small Cargo',
        'Cargueiro Grande', 'Large Cargo',
        'Nave Colonizadora', 'Nave de Colonização', 'Colony Ship',
        'Reciclador', 'Recycler',
        'Sonda de Espionagem', 'Espionage Probe',
        'Satélite Solar', 'Solar Satellite',
        'Rastejador', 'Crawler'
    )

    DEFENSES = (
        'Lançador de Mísseis',
        'Laser Ligeiro',
        'Laser Pesado',
        'Canhão de Gauss',
        'Canhão de Íons',
        'Canhão de Plasma',
        'Pequeno Escudo Planetário',
        'Grande Escudo Planetário',
        'Canhão de Iões'
    )

    NOISES = (
        '__________',
        'Depois da batalha',
        'Destruído',
        'roubou',
        'Metal',
        'Cristal',
        'Deutério',
        'perdeu',
        'total',
        'totais',
        'coordenada',
        'probabilidade',
        'reciclados',
        'lucros',
        'perdas',
        'perda',
        'Sumário',
        'Conversor',
    )

    SHIPS_REGEX = re.compile("|".join(SHIPS))
    DEFENSES_REGEX = re.compile("|".join(DEFENSES))
    NOISE_REGEX = re.compile("|".join(NOISES))
