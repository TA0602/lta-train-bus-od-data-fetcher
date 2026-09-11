# LTA Train OD Data Fetcher

Fetches Origin-Destination (OD) train passenger volume data from Singapore's
[LTA DataMall](https://datamall.lta.gov.sg/) `PV/ODTrain` API and publishes
it as multi-sheet Excel workbooks, committed to `data/`, uploaded as
workflow artifacts, and (once configured) emailed to you as download links.

## What it does

The `PV/ODTrain` endpoint doesn't return data rows directly — each call
(for a given `Date=YYYYMM`) returns a link to a ZIP file containing that
month's CSV of trip counts between stations. The pipeline queries the last
few months, downloads and extracts each available ZIP, merges them, and
builds two dated Excel workbooks per run:

```
data/lta_train_od_full_<start>_<end>_<run-timestamp>.xlsx   — all stations
data/lta_train_od_EW1_<start>_<end>_<run-timestamp>.xlsx    — station EW1 only
```

Both are split one sheet per month (so no sheet risks exceeding Excel's
1,048,576-row limit) and never overwrite a previous run's files.

Two GitHub Actions workflows keep this up to date — see
**[LTA_DATA_SETUP.md](LTA_DATA_SETUP.md)** for the full explanation:

- **Manual Fetch** — run on demand, always re-pulls the last 3-4 months and writes new files
- **Monthly Auto Fetch** — runs daily from the 11th to the last day of each month, skips
  API calls once that month's data is already covered, and retries daily
  until LTA publishes it

Every successful run also emails an HTML message with direct download
links to both workbooks, once SMTP secrets are configured (optional — see
setup guide; the files themselves are too large to attach directly).

## Files

- **`fetch_lta_data.py`** — fetches and merges historical OD train data into a CSV
- **`build_reports.py`** — converts CSV → multi-sheet Excel, optionally filtered by station
- **`pipeline_common.py`** — naming convention + "what's already covered" detection
- **`manual_pipeline.py`** / **`monthly_pipeline.py`** — orchestrators for each workflow
- **`requirements.txt`** — Python dependencies (`requests`, `openpyxl`)
- **`.github/workflows/`** — the two workflows described above
- **`LTA_DATA_SETUP.md`** — full setup guide, workflow details, and troubleshooting

## Quick start

```bash
pip install -r requirements.txt
python3 manual_pipeline.py "<YOUR_LTA_API_KEY>" 4
```

Writes the two dated workbooks into `data/`.

Get an API key from the [LTA DataMall Developer Portal](https://datamall.lta.gov.sg/content/datamall/en/request-for-api.html).

See **[LTA_DATA_SETUP.md](LTA_DATA_SETUP.md)** for the GitHub Actions
workflows, email setup, naming convention, and troubleshooting (including
API rate limits and LTA's documented 3-month data retention window).
