from statsmodels.tsa.statespace.sarimax import SARIMAX


def predict_player_future_score(sample, future_dates):
    y = sample['total']
    SARIMAXmodel = SARIMAX(y, order=(2, 1, 3), seasonal_order=(2, 1, 3, 26))
    SARIMAXmodel = SARIMAXmodel.fit()

    y_pred = SARIMAXmodel.get_forecast(len(future_dates))
    y_pred_df = y_pred.conf_int(alpha=0.05)
    y_pred_df['predictions'] = SARIMAXmodel.predict(start=y_pred_df.index[0], end=y_pred_df.index[-1])
    y_pred_df.index = future_dates.index

    return y_pred_df['predictions']
