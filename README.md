# LTA Train OD Data Fetcher

Fetches Origin-Destination (OD) train passenger volume data from Singapore's
[LTA DataMall](https://datamall.lta.gov.sg/) `PV/ODTrain` API and publishes
it as multi-sheet Excel workbooks (one sheet per month).

## What it does

The `PV/ODTrain` endpoint doesn't return data rows directly — each call
(for a given `Date=YYYYMM`) returns a link to a ZIP file containing that
month's CSV of trip counts between stations. The pipeline queries the last
few months, downloads and extracts each available ZIP, merges them, and
builds two Excel workbooks:

- **`lta_train_od_historical_by_month.xlsx`** — all stations
- **`lta_train_od_EW1_by_month.xlsx`** — filtered to station `EW1` only

Both are split one sheet per month so no sheet risks exceeding Excel's
1,048,576-row limit.

Two GitHub Actions workflows keep this up to date — see
**[LTA_DATA_SETUP.md](LTA_DATA_SETUP.md)** for the full explanation:

- **Manual Fetch** — run on demand, always re-pulls the last 3-4 months
- **Monthly Auto Fetch** — runs daily from the 11th–20th of each month, skips
  API calls once that month's data is already committed, and retries daily
  until LTA publishes it

## Files

- **`fetch_lta_data.py`** — fetches and merges historical OD train data into a CSV
- **`build_reports.py`** — converts CSV → multi-sheet Excel, optionally filtered by station
- **`monthly_pipeline.py`** — orchestrator for the scheduled workflow (idempotent, quota-aware)
- **`requirements.txt`** — Python dependencies (`requests`, `openpyxl`)
- **`.github/workflows/`** — the two workflows described above
- **`LTA_DATA_SETUP.md`** — full setup guide, workflow details, and troubleshooting

## Quick start

```bash
pip install -r requirements.txt
python3 fetch_lta_data.py "<YOUR_LTA_API_KEY>" "lta_train_od_historical.csv" 4
python3 build_reports.py lta_train_od_historical.csv lta_train_od_historical_by_month.xlsx
python3 build_reports.py lta_train_od_historical.csv lta_train_od_EW1_by_month.xlsx EW1
```

Get an API key from the [LTA DataMall Developer Portal](https://datamall.lta.gov.sg/content/datamall/en/request-for-api.html).

See **[LTA_DATA_SETUP.md](LTA_DATA_SETUP.md)** for the GitHub Actions
workflows, output file details, and troubleshooting (including API rate
limits and LTA's documented 3-month data retention window).
