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

    return df
