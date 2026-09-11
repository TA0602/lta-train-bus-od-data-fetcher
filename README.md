# LTA Train OD Data Fetcher

Fetches Origin-Destination (OD) train passenger volume data from Singapore's
[LTA DataMall](https://datamall.lta.gov.sg/) `PV/ODTrain` API and saves it as
a CSV file.

## What it does

The `PV/ODTrain` endpoint doesn't return data rows directly — each call
(for a given `Date=YYYYMM`) returns a link to a ZIP file containing that
month's CSV of trip counts between stations. `fetch_lta_data.py` queries a
range of recent months, downloads and extracts each available ZIP, and
merges everything into one combined CSV (LTA only keeps a rolling window of
recent months available; older months return no data).

## Files

- **`fetch_lta_data.py`** — the fetcher script
- **`requirements.txt`** — Python dependencies (just `requests`)
- **`.github/workflows/fetch-lta-data.yml`** — GitHub Actions workflow to run the fetcher on demand and publish the result
- **`LTA_DATA_SETUP.md`** — full setup guide, troubleshooting, and how to get the output file

## Quick start

```bash
pip install -r requirements.txt
python3 fetch_lta_data.py "<YOUR_LTA_API_KEY>" "lta_train_od_historical.csv" 4
```

Arguments: API key, output filename, number of months to look back (all optional, shown with defaults).

Get an API key from the [LTA DataMall Developer Portal](https://datamall.lta.gov.sg/content/datamall/en/request-for-api.html).

See **[LTA_DATA_SETUP.md](LTA_DATA_SETUP.md)** for the GitHub Actions
workflow, downloading results, and troubleshooting (including API rate
limits).
