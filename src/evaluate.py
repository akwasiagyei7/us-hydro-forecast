"""
Rolling-origin evaluation of one-month-ahead hydropower generation forecasts.

Train: 2011-2019 (2010 lost to lags).  Test: 2020-2024 (60 months) per plant.
Metrics: MAE, RMSE, and MAPE-like 'nMAE' = MAE / mean actual generation,
plus a 'dry-season' nMAE restricted to the driest 25% of test months by
streamflow, since that is when operators most need accurate forecasts.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from models import (FLOW_FEATURES, LAG_FEATURES, climatology, fit_predict_tree,
                    sarima_one_step, sarimax_one_step, seasonal_naive)
from plants import PLANTS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)
TEST_START = "2020-01-01"


def metrics(y, yhat):
    mask = ~(np.isnan(y) | np.isnan(yhat))
    y, yhat = y[mask], yhat[mask]
    e = y - yhat
    return dict(MAE=np.mean(np.abs(e)), RMSE=np.sqrt(np.mean(e ** 2)),
                nMAE=np.mean(np.abs(e)) / np.mean(y), n=int(mask.sum()))


def run_plant(df: pd.DataFrame, pid: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    d = df[df.plant_id == pid].dropna(subset=LAG_FEATURES + ["net_gen_mwh"]).copy()
    d = d.set_index("date")
    train, test = d[d.index < TEST_START], d[d.index >= TEST_START]
    y_tr, y_te = train["net_gen_mwh"], test["net_gen_mwh"]
    logflow_tr = np.log1p(train[["flow_mean_cfs"]])
    logflow_te = np.log1p(test[["flow_mean_cfs"]])

    preds = {
        "Seasonal naive": seasonal_naive(y_tr.combine_first(y_te), y_te.index),
        "Climatology": climatology(y_tr, y_te.index),
        "SARIMA": sarima_one_step(y_tr, y_te),
        "Random forest (lags)": fit_predict_tree("rf", train, test, LAG_FEATURES),
        "Gradient boosting (lags)": fit_predict_tree("gbm", train, test, LAG_FEATURES),
        "SARIMAX (+ current flow)": sarimax_one_step(y_tr, logflow_tr, y_te, logflow_te),
        "Random forest (+ current flow)": fit_predict_tree("rf", train, test, FLOW_FEATURES),
        "Gradient boosting (+ current flow)": fit_predict_tree("gbm", train, test, FLOW_FEATURES),
    }
    dry = test["flow_mean_cfs"] <= test["flow_mean_cfs"].quantile(0.25)
    rows = []
    for name, p in preds.items():
        m = metrics(y_te.values, p)
        m_dry = metrics(y_te[dry].values, p[dry.values])
        rows.append(dict(plant_id=pid, plant=PLANTS[pid]["name"], model=name,
                         **m, dry_nMAE=m_dry["nMAE"]))
    pred_df = pd.DataFrame(preds, index=y_te.index)
    pred_df.insert(0, "actual", y_te)
    pred_df.insert(0, "plant", PLANTS[pid]["name"])
    return pd.DataFrame(rows), pred_df


def plot_plant(pred_df: pd.DataFrame, pid: int):
    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.plot(pred_df.index, pred_df["actual"] / 1e3, color="black", lw=2, label="Actual (EIA-923)")
    for col, c in [("Seasonal naive", "tab:gray"), ("SARIMA", "tab:blue"),
                   ("Gradient boosting (lags)", "tab:orange"),
                   ("Gradient boosting (+ current flow)", "tab:green")]:
        ax.plot(pred_df.index, pred_df[col] / 1e3, lw=1.3, label=col, color=c)
    ax.set_title(f"{PLANTS[pid]['name']} ({PLANTS[pid]['state']}) — one-month-ahead forecasts, 2020–2024")
    ax.set_ylabel("Net generation (GWh)")
    ax.legend(ncol=3, fontsize=8, loc="upper left")
    ax.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(OUT / f"forecast_{pid}_{PLANTS[pid]['name'].replace(' ', '_').replace('(', '').replace(')', '')}.png", dpi=130)
    plt.close(fig)


def main():
    df = pd.read_csv(ROOT / "data/processed/model_dataset.csv", parse_dates=["date"])
    all_res, all_pred = [], []
    for pid in PLANTS:
        print("evaluating", PLANTS[pid]["name"])
        res, pred = run_plant(df, pid)
        all_res.append(res)
        all_pred.append(pred)
        plot_plant(pred, pid)
    res = pd.concat(all_res, ignore_index=True)
    res.to_csv(OUT / "results_by_plant.csv", index=False)
    pd.concat(all_pred).to_csv(OUT / "predictions_2020_2024.csv")

    summary = (res.groupby("model")[["nMAE", "dry_nMAE"]].mean()
                  .sort_values("nMAE").round(3))
    summary.to_csv(OUT / "results_summary.csv")
    print("\nAverage across plants (lower is better):")
    print(summary.to_string())

    # summary bar chart
    fig, ax = plt.subplots(figsize=(9, 4.5))
    summary[["nMAE", "dry_nMAE"]].plot.barh(ax=ax, color=["tab:blue", "tab:red"])
    ax.set_xlabel("Normalized MAE (MAE / mean generation), average of 8 plants")
    ax.set_title("One-month-ahead forecast error, test period 2020–2024")
    ax.legend(["All months", "Driest 25% of months"])
    ax.invert_yaxis(); ax.grid(axis="x", alpha=.3)
    fig.tight_layout(); fig.savefig(OUT / "model_comparison.png", dpi=130)


if __name__ == "__main__":
    main()
