from datetime import datetime, timedelta
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import pytz
from ogame.types import CompressedDict


class FleetHashMap:
    def __init__(self):
        self.available_ships = {
            'LIGHT_FIGHTER': 'Light Fighter',
            'HEAVY_FIGHTER': 'Heavy Fighter',
            'CRUISER': 'Cruiser',
            'BATTLESHIP': 'Battleship',
            'BATTLECRUISER': 'Battlecruiser',
            'DESTROYER': 'Destroyer',
            'DEATHSTAR': 'Deathstar',
            'BOMBER': 'Bomber',
            'REAPER': 'Reaper',
            'PATHFINDER': 'Pathfinder',
            'SMALL_CARGO': 'Small Cargo',
            'LARGE_CARGO': 'Large Cargo',
            'COLONY_SHIP': 'Colony Ship',
            'RECYCLER': 'Recycler',
            'ESPIONAGE_PROBE': 'Espionage Probe',
        }

    def validate_input_keys(self, keys):
        return all(k in self.available_ships for k in keys)

    def convert_input_keys(self, data):
        return {self.available_ships[k]: v for k, v in data.items()}


def fleet_mapping():
    ships_to_int = {
        'Light Fighter': 1,
        'Caça Ligeiro': 1,
        'Heavy Fighter': 2,
        'Caça Pesado': 2,
        'Cruiser': 3,
        'Cruzador': 3,
        'Battleship': 4,
        'Nave de Batalha': 4,
        'Battlecruiser': 5,
        'Interceptor': 5,
        'Interceptador': 5,
        'Destroyer': 6,
        'Destruidor': 6,
        'EDM': 7,
        'Death Star': 7,
        'Deathstar': 7,
        'Estrela da Morte': 7,
        'Bomber': 8,
        'Bombardeiro': 8,
        'Ceifeira': 9,
        'Reaper': 9,
        'Explorador': 10,
        'Pathfinder': 10,
        'Small Cargo': 11,
        'Cargueiro Pequeno': 11,
        'Large Cargo': 12,
        'Cargueiro Grande': 12,
        'Colony Ship': 13,
        'Nave de Colonização': 13,
        'Nave Colonizadora': 13,
        'Recycler': 14,
        'Reciclador': 14,
        'Espionage Probe': 15,
        'Sonda de Espionagem': 15,
    }
    int_to_ships = {v:k for k, v in ships_to_int.items()}
    return ships_to_int, int_to_ships


def day_to_int(weekday):
    conversion_table = {
        'Monday': 1,
        'Tuesday': 2,
        'Wednesday': 3,
        'Thursday': 4,
        'Friday': 5,
        'Saturday': 6,
        'Sunday': 7
    }
    return conversion_table.get(weekday, 0)


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


def get_activity_df(player_scores):
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
    # select rows which datetime is not NaN only
    df = df[df['datetime'].notna()]

    df['datetime'] = pd.to_datetime(df['datetime']).dt.tz_convert('America/Sao_Paulo')
    df['hour'] = df['datetime'].dt.strftime('%H').astype(int)
    df['weekday'] = df['datetime'].dt.strftime('%A')
    df['int_day'] = [day_to_int(i) for i in df.weekday.values]
    
    # ignore not found days (int day == 0)
    df = df.loc[df['int_day'] != 0]
    
    # get score diff
    df['DIFF'] = df.score.diff()
    df = df.fillna(0)

    return df


def get_future_activity(player_scores):
    df = get_activity_df(player_scores)

    # define an estimator and train it over player score diff 
    estimator = RandomForestRegressor()
    estimator.fit(df[['hour', 'int_day']].values, df.DIFF)

    # Generate one week ahead
    future_dates = pd.date_range(
        datetime.now().astimezone(pytz.timezone('America/Sao_Paulo')).replace(hour=0) + timedelta(days=1),
        periods=24*7,
        freq='H'
    )

    # transform future dates into model expected input type
    temp = [[i.strftime('%A'), i.hour, day_to_int(i.strftime('%A'))]
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


# def update_activity_pred_history(player):
#     """
#     Saves a week (7 days) activity prediction for future comparison
#     """
#     ...
