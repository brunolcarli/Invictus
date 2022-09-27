from datetime import datetime
import pandas as pd
from ogame.types import CompressedDict


def get_diff_df(player_scores):
    data = []
    for score in player_scores:
        try:
            dt = score.datetime
            total = CompressedDict.decompress_bytes(score.total)['score']
            economy = CompressedDict.decompress_bytes(score.economy)['score']
            research = CompressedDict.decompress_bytes(score.research)['score']
            military = CompressedDict.decompress_bytes(score.military)['score']
            ships = CompressedDict.decompress_bytes(score.military)['ships']
            military_built = CompressedDict.decompress_bytes(score.military_built)['score']
            military_dest = CompressedDict.decompress_bytes(score.military_destroyed)['score']
            military_lost = CompressedDict.decompress_bytes(score.military_lost)['score']
            honor = CompressedDict.decompress_bytes(score.honor)['score']

            data.append([dt, total, economy, research, military,
                        ships, military_built, military_dest, military_lost, honor])
        except:
            continue
    columns = ['datetime', 'total', 'economy', 'research', 'military',
              'ships', 'military_built', 'military_destroyed', 'military_lost', 'honor']
    df = pd.DataFrame(data, columns=columns)
    if not data:
        return df

    df['datetime'] = pd.to_datetime(df['datetime'])
    # df = df.set_index('datetime')
    # df['weekday'] = df.index.strftime('%A')

    df['total'] = df.total.diff()
    df['economy'] = df.economy.diff()
    df['research'] = df.research.diff()
    df['military'] = df.military.diff()
    df['ships'] = df.ships.diff()
    df['military_built'] = df.military_built.diff()
    df['military_destroyed'] = df.military_destroyed.diff()
    df['military_lost'] = df.military_lost.diff()
    df['honor'] = df.honor.diff()

    df['total'].loc[df['total'] < 0] = 0
    df['economy'].loc[df['economy'] < 0] = 0
    df['research'].loc[df['research'] < 0] = 0
    df['military'].loc[df['military'] < 0] = 0
    df['ships'].loc[df['ships'] < 0] = 0
    df['military_built'].loc[df['military_built'] < 0] = 0
    df['military_destroyed'].loc[df['military_destroyed'] < 0] = 0
    df['military_lost'].loc[df['military_lost'] < 0] = 0
    df['honor'].loc[df['honor'] < 0] = 0

    return df


def get_prediction_df(player_scores):
    data = []
    for score in player_scores:
        try:
            dt = score.datetime
            total = CompressedDict.decompress_bytes(score.total)['score']
            data.append([dt, total])
        except:
            continue

    df = pd.DataFrame(data, columns=['datetime', 'total'])
    if not data:
        return df

    offset = 10  # constant hours to forecast
    generation_freq = str(3600*offset)+'S'  # interval of future datetimes generation

    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.set_index('datetime')
    df['date'] = df.index.round(freq=generation_freq)
    df = df[['total', 'date']].groupby('date').mean().fillna(0)

    future_dates = pd.date_range(datetime.now(), periods=15, freq=generation_freq)
    future_dates = pd.DataFrame(index=pd.to_datetime(future_dates, format='%Y-%m-%d'))

    return df, future_dates
