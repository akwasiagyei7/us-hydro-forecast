# How to put this on GitHub under your own account

Do this yourself, on your own computer, so the account, the commit dates and the
history are genuinely yours. Plan on about an hour the first day and 20 minutes a
day for the next few days.

## One-time setup

1. Create a free account at https://github.com (use your real name).
2. Install Git (https://git-scm.com) and Python 3.10+ (https://python.org).
3. On GitHub, click **New repository**, name it `us-hydro-forecast`, make it **Public**,
   do NOT tick "add a README" (you already have one). Copy the URL it gives you.

## Day 1 — code and README only

Unzip the project, open a terminal in the `us-hydro-forecast` folder, and run:

```bash
git init
git add README.md LICENSE requirements.txt .gitignore src/plants.py src/download_eia923.py src/download_usgs.py
git commit -m "Data loaders for EIA-923 hydro generation and USGS streamflow"
git branch -M main
git remote add origin <paste the URL from GitHub>
git push -u origin main
```

Then actually run the downloads so the data lives on your machine:

```bash
pip install -r requirements.txt
cd src
python download_eia923.py 2010 2024
python download_usgs.py
```

## Day 2 — dataset and models

```bash
git add src/build_dataset.py src/models.py
git commit -m "Join generation with streamflow; add SARIMA, SARIMAX, RF and GBM models"
git push
```

## Day 3 — evaluation and results

Run `python evaluate.py` yourself (so the outputs are produced on your machine), then:

```bash
git add src/evaluate.py outputs/*.png outputs/*.csv data/processed/model_dataset.csv data/processed/eia923_hydro_monthly.csv data/processed/usgs_monthly_flow.csv
git commit -m "Rolling-origin evaluation 2020-2024; results and charts"
git push
```

## Day 4 onward — make it yours

Pick one item from the README roadmap and do it. Even a small change counts:
add a ninth plant, try a different SARIMA order, add a precipitation feature,
or write a short `docs/results.md` explaining what you learned. Commit each one.

## For the RFE packet (Exhibit RFE-9 / RFE-10)

- Print the repository front page (README with the results table and chart).
- Print the **Commits** page showing dates.
- Print `outputs/model_comparison.png` and two plant charts.
- Write a 1–2 page summary in your own words: what data, what models, what you
  found, what is next. Sign and date it.

## Be ready to explain it

An officer, a professor, or an interviewer may ask about this work. Make sure you
can explain, in your own words: where the data comes from, what "one-month-ahead
with a rolling origin" means, why tree models with lagged flow beat SARIMA here,
and why all models do worse in dry months. Read through every file in `src/`
until that is comfortable. If anything is unclear, change it until it is yours.
