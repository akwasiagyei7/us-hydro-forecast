"""
Join monthly plant generation (EIA-923) with monthly streamflow at the
paired USGS gage, and add lag / calendar features used by the models.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from plants import PLANTS

PROC = Path(__file__).resolve().parents[1] / "data" / "processed"


def build() -> pd.DataFrame:
    gen = pd.read_csv(PROC / "eia923_hydro_monthly.csv", parse_dates=["date"])
    flow = pd.read_csv(PROC / "usgs_monthly_flow.csv", parse_dates=["date"],
                       dtype={"site": str})

    rows = []
    for pid, p in PLANTS.items():
        g = gen[gen.plant_id == pid][["date", "net_gen_mwh"]].copy()
        f = flow[flow.site == p["usgs_site"]][["date", "flow_mean_cfs", "flow_min_cfs", "flow_max_cfs"]]
        d = g.merge(f, on="date", how="left").sort_values("date")
        # short gage outages (a few months at most): interpolate in time
        for c in ("flow_mean_cfs", "flow_min_cfs", "flow_max_cfs"):
            d[c] = d[c].interpolate(limit=6, limit_direction="both")
        d["plant_id"] = pid
        d["plant_name"] = p["name"]
        rows.append(d)
    df = pd.concat(rows, ignore_index=True)

    df["year"] = df.date.dt.year
    df["month"] = df.date.dt.month
    df["month_sin"] = np.sin(2 * np.pi * df.month / 12)
    df["month_cos"] = np.cos(2 * np.pi * df.month / 12)

    g = df.groupby("plant_id")
    for k in (1, 2, 3, 12):
        df[f"gen_lag{k}"] = g["net_gen_mwh"].shift(k)
        df[f"flow_lag{k}"] = g["flow_mean_cfs"].shift(k)
    df["gen_roll3"] = g["net_gen_mwh"].transform(lambda s: s.shift(1).rolling(3).mean())
    df["flow_roll3"] = g["flow_mean_cfs"].transform(lambda s: s.shift(1).rolling(3).mean())
    df["flow_roll12"] = g["flow_mean_cfs"].transform(lambda s: s.shift(1).rolling(12).mean())

    out = PROC / "model_dataset.csv"
    df.to_csv(out, index=False)
    print(f"wrote {out}  ({len(df):,} rows, {df.plant_id.nunique()} plants, "
          f"{df.date.min().date()} to {df.date.max().date()})")
    return df


if __name__ == "__main__":
    build()
