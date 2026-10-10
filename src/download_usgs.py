"""
Download daily mean streamflow (parameter 00060, cubic feet per second)
from the USGS National Water Information System and aggregate to monthly.

Source: U.S. Geological Survey, NWIS Daily Values Web Service
https://waterservices.usgs.gov/
"""
import sys
from pathlib import Path

import pandas as pd
import requests

from plants import PLANTS

PROC = Path(__file__).resolve().parents[1] / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)
URL = "https://waterservices.usgs.gov/nwis/dv/"


def fetch_daily(site: str, start: str, end: str) -> pd.DataFrame:
    params = dict(format="json", sites=site, parameterCd="00060",
                  startDT=start, endDT=end, statCd="00003")
    r = requests.get(URL, params=params, timeout=120)
    r.raise_for_status()
    ts = r.json()["value"]["timeSeries"]
    if not ts:
        raise RuntimeError(f"no data returned for site {site}")
    vals = ts[0]["values"][0]["value"]
    df = pd.DataFrame(vals)[["dateTime", "value"]]
    df["date"] = pd.to_datetime(df["dateTime"].str[:10])
    df["flow_cfs"] = pd.to_numeric(df["value"], errors="coerce")
    df.loc[df.flow_cfs < 0, "flow_cfs"] = pd.NA   # USGS uses -999999 for missing
    df["site"] = site
    return df[["site", "date", "flow_cfs"]]


def main(start="2010-01-01", end="2024-12-31"):
    sites = sorted({p["usgs_site"] for p in PLANTS.values()})
    daily = pd.concat([fetch_daily(s, start, end) for s in sites], ignore_index=True)
    daily.to_csv(PROC / "usgs_daily_flow.csv", index=False)
    monthly = (daily.set_index("date").groupby("site")["flow_cfs"]
                    .resample("MS").agg(["mean", "min", "max", "count"]).reset_index())
    monthly.columns = ["site", "date", "flow_mean_cfs", "flow_min_cfs", "flow_max_cfs", "n_days"]
    monthly.to_csv(PROC / "usgs_monthly_flow.csv", index=False)
    print(f"wrote {len(daily):,} daily and {len(monthly):,} monthly rows for {len(sites)} gages")


if __name__ == "__main__":
    main(*sys.argv[1:])
