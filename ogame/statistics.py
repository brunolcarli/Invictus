from collections import Counter
import pandas as pd
import pytz
from ogame.types import CompressedDict
from ogame.util import fleet_mapping


def weekday_relative_freq(scores):
    data = []
    for score in scores:
        dt = score.datetime.astimezone(pytz.timezone('America/Sao_Paulo')).date()
        total = CompressedDict.decompress_bytes(score.total)['score']
        data.append([dt, total])

    # set up dataframe
    df = pd.DataFrame(data, columns=['DATE', 'TOTAL'])
    # get weekday names
    df['WEEKDAY'] = pd.to_datetime(df.DATE).dt.strftime('%A')
    df['F'] = df.WEEKDAY.value_counts(normalize=True)
    # calculate score difference
    df['DIFF'] = df.TOTAL.diff().fillna(0)
    # group diff sums by weekday
    df = df.groupby('WEEKDAY').sum()
    # calculate the relative frequency
    df['REL_FREQ'] = df['DIFF'] / df.DIFF.sum()

    # order dataframe with weekdays common sequence
    ordering = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df = df.reindex(ordering)

    # caulcutae positive and negative deviations
    df['POS_STD'] = df[['REL_FREQ', 'F']].T.var() + (df.REL_FREQ + df[['REL_FREQ', 'F']].T.std())
    df['NEG_STD'] = df[['REL_FREQ', 'F']].T.var() + (df.REL_FREQ - df[['REL_FREQ', 'F']].T.std())
    df[['REL_FREQ', 'POS_STD', 'NEG_STD']] = df[['REL_FREQ', 'POS_STD', 'NEG_STD']].clip(0)

    # transform to percentual
    df['REL_FREQ'] = df.REL_FREQ * 100
    df['POS_STD'] = df.POS_STD * 100
    df['NEG_STD'] = df.NEG_STD * 100

    # show only two decimals
    df['REL_FREQ'] = df['REL_FREQ'].round(2)
    df['POS_STD'] = df['POS_STD'].round(2)
    df['NEG_STD'] = df['NEG_STD'].round(2)


    return df.fillna(0)


def hour_relative_freq(scores, period):
    data = []
    for score in scores:
        dt = score.datetime.astimezone(pytz.timezone('America/Sao_Paulo'))
        total = CompressedDict.decompress_bytes(score.total)['score']
        data.append([dt, total])

    # set up dataframe
    df = pd.DataFrame(data, columns=['DATETIME', 'TOTAL'])
    df = df.set_index(df['DATETIME'])

    df['HOUR'] = df.index.round(freq=period).strftime('%H:'+'%M')
    df['F'] = df.HOUR.value_counts(normalize=True)
    # calculate score difference
    df['DIFF'] = df.TOTAL.diff().fillna(0)
    # group diff sums by time
    df = df[['DIFF', 'HOUR', 'F']].groupby('HOUR').sum()
    # calculate the relative frequency
    df['REL_FREQ'] = df['DIFF'] / df.DIFF.sum()

    # caulcutae positive and negative deviations
    df['POS_STD'] = df[['REL_FREQ', 'F']].T.var() + (df.REL_FREQ + df[['REL_FREQ', 'F']].T.std())
    df['NEG_STD'] = df[['REL_FREQ', 'F']].T.var() + (df.REL_FREQ - df[['REL_FREQ', 'F']].T.std())
    df[['REL_FREQ', 'POS_STD', 'NEG_STD']] = df[['REL_FREQ', 'POS_STD', 'NEG_STD']].clip(0)

    # transform to percentual
    df['REL_FREQ'] = df.REL_FREQ * 100
    df['POS_STD'] = df.POS_STD * 100
    df['NEG_STD'] = df.NEG_STD * 100

    # show only two decimals
    df['REL_FREQ'] = df['REL_FREQ'].round(2)
    df['POS_STD'] = df['POS_STD'].round(2)
    df['NEG_STD'] = df['NEG_STD'].round(2)

    return df.fillna(0)


def fleet_relative_freq(player):
    ship2int, int2ship = fleet_mapping()
    attack_instance = player.combat_report_attacker.all()
    defense_instance = player.combat_report_defender.all()
    fleet_records = player.player_fleet_record.all()

    fleet = {}
    for report in attack_instance:
        data = CompressedDict.decompress_bytes(report.attackers)
        for attacker in data:
            if player.name in attacker:
                for ship, number in data[attacker]['ships'].items():
                    try:
                        ship_key = ship2int[ship]
                    except KeyError:
                        continue
                    if ship_key not in fleet:
                        fleet[ship_key] = number
                    else:
                        fleet[ship_key] += number
                break

    for report in defense_instance:
        data = CompressedDict.decompress_bytes(report.defenders)
        for defender in data:
            if player.name in defender:
                for ship, number in data[defender]['ships'].items():
                    try:
                        ship_key = ship2int[ship]
                    except KeyError:
                        continue
                    if ship_key not in fleet:
                        fleet[ship_key] = number
                    else:
                        fleet[ship_key] += number
                break

    for record in fleet_records:
        data = CompressedDict.decompress_bytes(record.fleet)
        for ship, number in data.items():
            try:
                ship_key = ship2int[ship]
            except KeyError:
                continue
            if ship_key not in fleet:
                fleet[ship_key] = number
            else:
                fleet[ship_key] += number

    # Fill non existent ships with zero percentage
    for i in int2ship.keys():
        if i not in fleet:
            fleet[i] = 0

    data = []
    total_ships = sum(fleet.values())
    # avoid zero division error
    if total_ships == 0:
        total_ships = 1

    for int_ship, number in fleet.items():
        data.append([int2ship[int_ship], (number/total_ships) * 100])
    df = pd.DataFrame(data, columns=['SHIP', 'FREQ']).round(2)
    return df.set_index('SHIP').sort_index()


def universe_fleet_relative_freq(reports, fleet_records):
    ship2int, int2ship = fleet_mapping()

    fleet = {}
    for report in reports:
        data = CompressedDict.decompress_bytes(report.attackers)
        for attacker in data:
            for ship, number in data[attacker]['ships'].items():
                try:
                    ship_key = ship2int[ship]
                except KeyError:
                    continue
                if ship_key not in fleet:
                    fleet[ship_key] = number
                else:
                    fleet[ship_key] += number

        data = CompressedDict.decompress_bytes(report.defenders)
        for defender in data:
            for ship, number in data[defender]['ships'].items():
                try:
                    ship_key = ship2int[ship]
                except KeyError:
                    continue
                if ship_key not in fleet:
                    fleet[ship_key] = number
                else:
                    fleet[ship_key] += number

    for record in fleet_records:
        data = CompressedDict.decompress_bytes(record.fleet)
        for ship, number in data.items():
            try:
                ship_key = ship2int[ship]
            except KeyError:
                continue
            if ship_key not in fleet:
                fleet[ship_key] = number
            else:
                fleet[ship_key] += number

    # Fill non existent ships with zero percentage
    for i in int2ship.keys():
        if i not in fleet:
            fleet[i] = 0

    data = []
    total_ships = sum(fleet.values())
    # avoid zero division error
    if total_ships == 0:
        total_ships = 1

    for int_ship, number in fleet.items():
        data.append([int2ship[int_ship], (number/total_ships) * 100])
    df = pd.DataFrame(data, columns=['SHIP', 'FREQ']).round(2)
    return df.set_index('SHIP').sort_index()
