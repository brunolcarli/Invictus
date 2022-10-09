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
    # calculate score difference
    df['DIFF'] = df.TOTAL.diff().fillna(0)
    # group diff sums by weekday
    df = df.groupby('WEEKDAY').sum()
    # calculate the relative frequency
    df['REL_FREQ'] = df['DIFF'] / df.DIFF.sum()
    # transform to percentual
    df['REL_FREQ_PERC'] = df.REL_FREQ * 100
    # show only two decimals
    df['REL_FREQ_PERC'] = df['REL_FREQ_PERC'].round(2)

    # order dataframe with weekdays common sequence
    ordering = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df = df.reindex(ordering)

    # clip negatives
    df['REL_FREQ_PERC'] = df['REL_FREQ_PERC'].clip(0)

    return df


def halfhour_relative_freq(scores):
    data = []
    for score in scores:
        dt = score.datetime.astimezone(pytz.timezone('America/Sao_Paulo'))
        total = CompressedDict.decompress_bytes(score.total)['score']
        data.append([dt, total])

    # set up dataframe
    df = pd.DataFrame(data, columns=['DATETIME', 'TOTAL'])
    df = df.set_index(df['DATETIME'])

    # get rounded time by 30 minutes
    df['HALFHOUR'] = df.index.round(freq='1800S').strftime('%H:'+'%M')
    # calculate score difference
    df['DIFF'] = df.TOTAL.diff().fillna(0)
    # group diff sums by time
    df = df[['DIFF', 'HALFHOUR']].groupby('HALFHOUR').sum()
    # calculate the relative frequency
    df['REL_FREQ'] = df['DIFF'] / df.DIFF.sum()
    # transform to percentual
    df['REL_FREQ_PERC'] = df.REL_FREQ * 100
    # show only two decimals
    df['REL_FREQ_PERC'] = df['REL_FREQ_PERC'].round(2)

    # clip negatives
    df['REL_FREQ_PERC'] = df['REL_FREQ_PERC'].clip(0)

    return df
