"""
Download EIA-923 annual files and extract monthly net generation
for conventional hydroelectric plants (fuel type WAT, prime mover HY).

Source: U.S. Energy Information Administration, Form EIA-923
https://www.eia.gov/electricity/data/eia923/
"""
import io
import re
import sys
import zipfile
from pathlib import Path

import pandas as pd
import requests

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

BASE = "https://www.eia.gov/electricity/data/eia923/"
MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


def file_url(year: int, latest_years=(2025, 2026)) -> str:
    sub = "xls/" if year in latest_years else "archive/xls/"
    return f"{BASE}{sub}f923_{year}.zip"


def download_year(year: int) -> Path:
    out = RAW / f"f923_{year}.zip"
    if out.exists():
        return out
    url = file_url(year)
    print(f"downloading {url}")
    r = requests.get(url, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)
    return out


def _find_generation_sheet(zf: zipfile.ZipFile) -> str:
    # The generation & fuel workbook is named like
    # "EIA923_Schedules_2_3_4_5_M_12_2019_Final_Revision.xlsx"
    cands = [n for n in zf.namelist()
             if re.search(r"schedules[ _]2[ _]3[ _]4[ _]5", n, re.I) and n.lower().endswith((".xlsx", ".xls"))]
    if not cands:
        raise RuntimeError(f"no generation workbook in zip: {zf.namelist()}")
    return sorted(cands)[-1]


def extract_hydro(year: int) -> pd.DataFrame:
    zpath = download_year(year)
    with zipfile.ZipFile(zpath) as zf:
        name = _find_generation_sheet(zf)
        raw = zf.read(name)
    # locate the header row (it moved between years: row 7 in 2010, row 5 later)
    probe = pd.read_excel(io.BytesIO(raw), sheet_name=0, header=None, nrows=10)
    hdr = next(i for i in range(len(probe))
               if any(str(x).strip().lower().startswith("plant id") for x in probe.iloc[i]))
    df = pd.read_excel(io.BytesIO(raw), sheet_name=0, header=hdr)
    df.columns = [re.sub(r"\s+", " ", str(c)).strip() for c in df.columns]

    col_plant = next(c for c in df.columns if c.lower().startswith("plant id"))
    col_name = next(c for c in df.columns if c.lower().startswith("plant name"))
    col_state = next(c for c in df.columns if c.lower() in ("plant state", "state"))
    col_fuel = next(c for c in df.columns if c.lower().startswith("reported fuel type"))
    col_pm = next(c for c in df.columns if c.lower().startswith("reported prime mover"))
    gen_cols = {}
    for m in MONTHS:
        # "Netgen January" (2011+) or "NETGEN_JAN" (2010)
        gen_cols[m] = next(c for c in df.columns
                           if c.lower() in (f"netgen {m.lower()}", f"netgen_{m[:3].lower()}"))

    hydro = df[(df[col_fuel] == "WAT") & (df[col_pm] == "HY")].copy()
    long = hydro.melt(id_vars=[col_plant, col_name, col_state],
                      value_vars=list(gen_cols.values()),
                      var_name="month_col", value_name="net_gen_mwh")
    inv = {v: i + 1 for i, (m, v) in enumerate(gen_cols.items())}
    long["month"] = long["month_col"].map(inv)
    long["year"] = year
    long = long.rename(columns={col_plant: "plant_id", col_name: "plant_name",
                                col_state: "state"})
    long["net_gen_mwh"] = pd.to_numeric(long["net_gen_mwh"], errors="coerce")
    # a plant can have several rows (e.g. multiple reporting units); sum them
    out = (long.groupby(["plant_id", "plant_name", "state", "year", "month"], as_index=False)
               ["net_gen_mwh"].sum())
    out["date"] = pd.to_datetime(dict(year=out.year, month=out.month, day=1))
    return out[["plant_id", "plant_name", "state", "date", "net_gen_mwh"]]


def main(years):
    frames = [extract_hydro(y) for y in years]
    allyrs = pd.concat(frames, ignore_index=True).sort_values(["plant_id", "date"])
    dest = RAW.parent / "processed" / "eia923_hydro_monthly.csv"
    dest.parent.mkdir(exist_ok=True)
    allyrs.to_csv(dest, index=False)
    print(f"wrote {dest}  ({len(allyrs):,} rows, "
          f"{allyrs.plant_id.nunique():,} plants, {years[0]}-{years[-1]})")


if __name__ == "__main__":
    if len(sys.argv) == 3:
        years = list(range(int(sys.argv[1]), int(sys.argv[2]) + 1))
    else:
        years = list(range(2010, 2025))
    main(years)
