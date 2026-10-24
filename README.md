# U.S. Hydropower Generation Forecasting

**Statistical forecasting and machine learning with public U.S. energy and streamflow data**

**Author:** Akwasi Agyei | Master of Statistics, North Carolina State University  
**Status:** Phase 1 research benchmark (October 2026). This is an exploratory project, not an operational forecasting service.

## Project overview

This project compares statistical and machine learning approaches for predicting monthly electricity generation at eight hydropower plants in the southeastern United States. It combines plant-level generation from the U.S. Energy Information Administration (EIA) with streamflow observations from the U.S. Geological Survey (USGS).

My interest in this subject began with hydropower forecasting research in Ghana. I am extending that work to publicly available U.S. data to study how historical generation and river flow can support energy planning, particularly during dry periods.

**Research question:** How accurately can we forecast a plant's next month of hydropower generation using its historical generation, streamflow and seasonal patterns?

## Data and tools

| Source | Data | Period used |
|---|---|---|
| [EIA Form 923](https://www.eia.gov/electricity/data/eia923/) | Monthly net electricity generation by plant (MWh) | 2010–2024 |
| [USGS water services](https://waterservices.usgs.gov/) | Daily streamflow (cfs), aggregated to monthly statistics | 2010–2024 |

The sample covers eight plants in North Carolina, South Carolina and the Savannah/Roanoke river basins. Plant identifiers and paired USGS gages are documented in [`src/plants.py`](src/plants.py).

**Technical skills demonstrated:** Python, pandas, NumPy, time-series forecasting, feature engineering, scikit-learn, statsmodels, model evaluation, data integration and Matplotlib.

## Approach

1. Download and clean monthly EIA plant-generation records and USGS streamflow measurements.
2. Pair each plant with a nearby/upstream streamflow gage and build monthly lagged and seasonal features.
3. Compare seasonal naive and historical monthly-average baselines with SARIMA, SARIMAX, random forest and gradient boosting.
4. Evaluate predictions against observed generation for **January 2020–December 2024** (60 months per plant). Training data start in 2011 after lag construction.
5. Compare errors across all test months and the driest 25% of months at each plant.

**Evaluation design:** SARIMA and SARIMAX are refitted as each observed test month becomes available. Random forest and gradient boosting are fitted once on the 2011–2019 training period and evaluated using lagged observations for each test month. The tree-model procedure is therefore **not** a monthly rolling refit, although it uses observed history for one-step-ahead predictions.

**Important distinction:** Models marked **“+ current flow”** use the actual streamflow measured during the month being predicted. These are **retrospective comparisons, not deployable one-month-ahead forecasts**. The lag-only models are the more appropriate comparison for a forecast made before the target month begins.

## Benchmark results

Average normalized mean absolute error (**nMAE = MAE / average actual generation**) across the eight plants; **lower is better**. Values below are taken from [`outputs/results_summary.csv`](outputs/results_summary.csv).

| Model | All test months | Driest 25% |
|---|---:|---:|
| Random forest (+ current flow) | 0.269 | 0.310 |
| Gradient boosting (+ current flow) | 0.284 | 0.314 |
| **Random forest (lags only)** | **0.315** | **0.384** |
| Gradient boosting (lags only) | 0.328 | 0.392 |
| SARIMAX (+ current flow) | 0.342 | 0.407 |
| SARIMA | 0.352 | 0.415 |
| Climatology (monthly historical mean) | 0.383 | 0.460 |
| Seasonal naive | 0.449 | 0.502 |

The lag-only random forest achieved a **0.315 nMAE**, approximately **10.5% lower** than SARIMA (0.352) and **29.8% lower** than seasonal naive (0.449), using these reported average errors. Results varied by plant and should not be generalized without further validation.

![Benchmark model comparison](outputs/model_comparison.png)

### Example: Fontana Dam, North Carolina

![Fontana Dam generation and model predictions](outputs/forecast_2779_Fontana_Dam.png)

Detailed results: [per-plant error table](outputs/results_by_plant.csv) · [saved predictions](outputs/predictions_2020_2024.csv).

## Reproduce the analysis

Use Python 3.10+ in a virtual environment. From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\\Scripts\\activate
python -m pip install -r requirements.txt

cd src
python download_eia923.py 2010 2024
python download_usgs.py
python build_dataset.py
python evaluate.py
```

The scripts retrieve public data, prepare the dataset and regenerate tables and figures in `outputs/`. Downloads require an internet connection and may take time or change if source files are revised. Alternatively, inspect [`notebooks/run_pipeline.ipynb`](notebooks/run_pipeline.ipynb).

## Limitations and next steps

- **Data availability and leakage:** Streamflow gaps are interpolated in the current pipeline, including bidirectional interpolation. This should be revised to a strictly past-only procedure before treating the study as a fully leakage-controlled prospective benchmark.
- **Gage selection:** Paired USGS gages are hydrologic proxies and may not precisely represent inflow at every dam.
- **Model comparisons:** The tree models are not refitted monthly, and no production forecast of future streamflow is supplied. “+ current flow” figures should not be compared with operational forecast accuracy.
- **Scope:** Results reflect eight selected plants and a 2020–2024 retrospective test window.

Planned enhancements include leakage-safe validation, hydrologic feature checks, NOAA precipitation and drought indicators, forecast streamflow inputs, longer forecast horizons and prediction intervals.

## Related research

- [Forecasting hydropower generation and reservoir level using ARIMA (2022)](https://doi.org/10.5539/ijsp.v11n5p30)
- [Structural VAR study of hydropower-related variables (2022)](https://doi.org/10.5539/ijsp.v11n3p22)

## License

Code: [MIT License](LICENSE). Source datasets are publicly available from EIA and USGS; acknowledge the original agencies when reusing them.

**Contact:** akwasiagyei489@gmail.com
