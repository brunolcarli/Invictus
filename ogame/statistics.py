import pandas as pd
import pytz
from ogame.types import CompressedDict


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

    # calculate variance
    df['VAR'] = df[['REL_FREQ', 'F']].T.var()
    # calculate std deviation
    df['STD'] = df[['REL_FREQ', 'F']].T.std()

    # transform to percentual
    df['REL_FREQ'] = df.REL_FREQ * 100
    df['VAR'] = df.VAR * 100
    df['STD'] = df.STD * 100

    # show only two decimals
    df['REL_FREQ'] = df['REL_FREQ'].round(2)
    df['VAR'] = df['VAR'].round(2)
    df['STD'] = df['STD'].round(2)

    # clip negatives
    df['REL_FREQ'] = df['REL_FREQ'].clip(0)
    df['VAR'] = df['VAR'].clip(0)
    df['STD'] = df['STD'].clip(0)

    return df


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

    # calculate variance
    df['VAR'] = df[['REL_FREQ', 'F']].T.var()
    # calculate std deviation
    df['STD'] = df[['REL_FREQ', 'F']].T.std()

    # transform to percentual
    df['REL_FREQ'] = df.REL_FREQ * 100
    df['VAR'] = df.VAR * 100
    df['STD'] = df.STD * 100

    # show only two decimals
    df['REL_FREQ'] = df['REL_FREQ'].round(2)
    df['VAR'] = df['VAR'].round(2)
    df['STD'] = df['STD'].round(2)

    # clip negatives
    df['REL_FREQ'] = df['REL_FREQ'].clip(0)
    df['VAR'] = df['VAR'].clip(0)
    df['STD'] = df['STD'].clip(0)

    return df
