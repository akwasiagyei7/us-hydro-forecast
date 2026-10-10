"""
Forecasting models for monthly hydropower generation.

All models forecast one month ahead using only information available
at the end of the previous month (lagged generation and lagged streamflow).
The '+ current flow' variants also use the current month's streamflow;
they are an upper bound showing how much a good inflow forecast would help.
"""
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from statsmodels.tsa.statespace.sarimax import SARIMAX

warnings.filterwarnings("ignore")

LAG_FEATURES = ["gen_lag1", "gen_lag2", "gen_lag3", "gen_lag12", "gen_roll3",
                "flow_lag1", "flow_lag2", "flow_lag3", "flow_lag12",
                "flow_roll3", "flow_roll12", "month_sin", "month_cos"]
FLOW_FEATURES = LAG_FEATURES + ["flow_mean_cfs", "flow_min_cfs", "flow_max_cfs"]


def seasonal_naive(series: pd.Series, horizon_dates: pd.DatetimeIndex) -> np.ndarray:
    """Forecast = generation in the same month one year earlier."""
    return np.array([series.get(d - pd.DateOffset(years=1), np.nan) for d in horizon_dates])


def climatology(train: pd.Series, horizon_dates: pd.DatetimeIndex) -> np.ndarray:
    """Forecast = long-run average for that calendar month (training years only)."""
    m = train.groupby(train.index.month).mean()
    return np.array([m.get(d.month, np.nan) for d in horizon_dates])


def _fit(y, x=None, order=(1, 0, 1), seasonal_order=(1, 1, 0, 12)):
    return SARIMAX(y.values, exog=None if x is None else x.values,
                   order=order, seasonal_order=seasonal_order,
                   enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)


def sarima_one_step(train: pd.Series, test: pd.Series) -> np.ndarray:
    """Rolling-origin one-step-ahead SARIMA(1,0,1)(1,1,0)12, refit each month."""
    preds, hist = [], train.copy()
    for d, y in test.items():
        res = _fit(hist)
        preds.append(float(res.forecast(1)[0]))
        hist.loc[d] = y
    return np.array(preds)


def sarimax_one_step(train_y, train_x, test_y, test_x) -> np.ndarray:
    """Same as sarima_one_step but with log streamflow as an exogenous input."""
    preds, hy, hx = [], train_y.copy(), train_x.copy()
    for d, y in test_y.items():
        res = _fit(hy, hx)
        preds.append(float(res.forecast(1, exog=test_x.loc[[d]].values)[0]))
        hy.loc[d] = y
        hx.loc[d] = test_x.loc[d]
    return np.array(preds)


def tree_model(kind: str):
    if kind == "rf":
        return RandomForestRegressor(n_estimators=500, min_samples_leaf=3,
                                     random_state=0, n_jobs=-1)
    if kind == "gbm":
        return GradientBoostingRegressor(n_estimators=400, learning_rate=0.03,
                                         max_depth=3, subsample=0.8, random_state=0)
    raise ValueError(kind)


def fit_predict_tree(kind, train: pd.DataFrame, test: pd.DataFrame, features) -> np.ndarray:
    """Tree models trained once on 2011-2019 and applied to 2020-2024."""
    m = tree_model(kind)
    m.fit(train[features], train["net_gen_mwh"])
    return m.predict(test[features])
