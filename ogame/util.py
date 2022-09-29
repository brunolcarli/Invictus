from datetime import datetime
import pandas as pd
import pytz
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

    df[columns[1:]] = df[columns[1:]].diff().fillna(0)
    df['total'].loc[df['total'] < 0] = 0
    df['economy'].loc[df['economy'] < 0] = 0
    df['research'].loc[df['research'] < 0] = 0
    df['military'].loc[df['military'] < 0] = 0
    df['ships'].loc[df['ships'] < 0] = 0
    df['military_built'].loc[df['military_built'] < 0] = 0
    df['military_destroyed'].loc[df['military_destroyed'] < 0] = 0
    df['military_lost'].loc[df['military_lost'] < 0] = 0
    df['honor'].loc[df['honor'] < 0] = 0
    df['datetime'] = pd.to_datetime(df['datetime']).dt.tz_convert('America/Sao_Paulo')
    

    return df


def get_prediction_df(player_scores):
    data = []
    totals = []
    for score in player_scores:
        try:
            dt = score.datetime
            total = CompressedDict.decompress_bytes(score.total)['score']
            data.append([dt, total])
            totals.append(total)
        except:
            continue

    df = pd.DataFrame(data, columns=['datetime', 'total'])
    if not data:
        return df, [], totals

    offset = 11  # constant hours to forecast
    generation_freq = str(3600*offset)+'S'  # interval of future datetimes generation

    df['datetime'] = pd.to_datetime(df['datetime']).dt.tz_convert('America/Sao_Paulo')
    df = df.set_index('datetime')
    df['date'] = df.index.round(freq=generation_freq)
    df = df[['total', 'date']].groupby('date').mean().fillna(0)

    now = datetime.now().astimezone(pytz.timezone('America/Sao_Paulo'))
    future_dates = pd.date_range(now, periods=14, freq=generation_freq).tz_convert('America/Sao_Paulo')
    future_dates = pd.DataFrame(index=future_dates)

    return df, future_dates, totals[-len(df):]
