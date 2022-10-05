from datetime import datetime, timedelta
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
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
    df[columns[1:]] = df[columns[1:]].clip(0)
    df['datetime'] = pd.to_datetime(df['datetime']).dt.tz_convert('America/Sao_Paulo')

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
        return df, []

    offset = 11  # constant hours to forecast
    generation_freq = str(3600*offset)+'S'  # interval of future datetimes generation

    df['datetime'] = pd.to_datetime(df['datetime']).dt.tz_convert('America/Sao_Paulo')
    df = df.set_index('datetime')
    df['date'] = df.index.round(freq=generation_freq)
    df = df[['total', 'date']].groupby('date').mean().fillna(0)

    now = datetime.now().astimezone(pytz.timezone('America/Sao_Paulo'))
    future_dates = pd.date_range(now, periods=14, freq=generation_freq).tz_convert('America/Sao_Paulo')
    future_dates = pd.DataFrame(index=future_dates)

    return df, future_dates


def get_future_activity(player_scores):
    data = []
    datetimes = []
    for score in player_scores:
        try:
            dt = score.datetime
            total = CompressedDict.decompress_bytes(score.total)['score']
            data.append([dt, total])
            datetimes.append(dt)
        except:
            continue

    # set up dataframe indexed by dayhours
    df = pd.DataFrame(
        data, columns=['datetime', 'score'],
        index=pd.to_datetime(datetimes).tz_convert('America/Sao_Paulo').strftime('%H')
    )
    day_to_int = {
        'Monday': 1,
        'Tuesday': 2,
        'Wednesday': 3,
        'Thursday': 4,
        'Friday': 5,
        'Saturday': 6,
        'Sunday': 7
    }
    df['datetime'] = pd.to_datetime(df['datetime']).dt.tz_convert('America/Sao_Paulo')
    df['hour'] = df['datetime'].dt.strftime('%H').astype(int)
    df['weekday'] = df['datetime'].dt.strftime('%A')
    df['int_day'] = [day_to_int.get(i, 0) for i in df.weekday.values]
    
    # ignore not found days (int day == 0)
    df = df.loc[df['int_day'] != 0]
    
    # get score diff
    df['DIFF'] = df.score.diff()

    # define an estimator and train it over player score diff 
    estimator = RandomForestRegressor()
    estimator.fit(df[['hour', 'int_day']].values[1:], df.DIFF[1:])  # the 0 index is a NaN

    # Generate one week ahead
    future_dates = pd.date_range(
        datetime.now().astimezone(pytz.timezone('America/Sao_Paulo')).replace(hour=0) + timedelta(days=1),
        periods=24*7,
        freq='H'
    )

    # transform future dates into model expected input type
    temp = [[i.strftime('%A'), i.hour, day_to_int[i.strftime('%A')]]
                    for i in future_dates]

    # slice transformed data into ach next week day with 24 hours each day
    offset = 24
    X_input = [temp[i:i+offset] for i in range(0, len(temp), offset)]

    # Create a new dataframe with pretions to each future weekday
    preds = pd.DataFrame()
    for day in X_input:
        col = []
        for point in day:
            col.append(estimator.predict([point[1:]])[0])
        preds[point[0]] = col

    preds = preds.clip(0)
    return preds
