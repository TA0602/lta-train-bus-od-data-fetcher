# LTA Train Historical Data Setup Guide

This guide explains how this repo fetches Singapore LTA train
Origin-Destination (OD) data from the `PV/ODTrain` DataMall API and
publishes it as Excel workbooks.

## How the API Actually Works

The `PV/ODTrain` endpoint does **not** return data rows directly. Each call
(with a `Date=YYYYMM` query parameter) returns a JSON object containing a
**link to a ZIP file** holding a CSV of OD trip counts for that month:

```json
{ "value": [ { "Link": "https://.../PVODTrain202401.zip" } ] }
```

`fetch_lta_data.py` queries a range of months, downloads each available ZIP,
extracts the CSV inside, tags each row with its source month, and merges
everything into one combined CSV. Per LTA's own API documentation, each
Passenger Volume API "requests for files up to last three months" and
publishes the previous month's data by the 10th of the following month —
confirmed empirically too (older months 404).

## What's Included

- **fetch_lta_data.py** — fetches and merges historical OD train data into a CSV
- **build_reports.py** — converts that CSV into a multi-sheet Excel workbook (one sheet per month), optionally filtered to one station code
- **monthly_pipeline.py** — orchestrator for the scheduled workflow: skips API calls entirely if the target month is already committed, otherwise fetches + rebuilds the reports
- **requirements.txt** — Python dependencies (`requests`, `openpyxl`)
- **.github/workflows/fetch-lta-data-manual.yml** — on-demand workflow
- **.github/workflows/fetch-lta-data-monthly.yml** — scheduled workflow

## Output Files

Every successful run (manual or scheduled) produces two workbooks, each
with **one sheet per month** (so no single sheet ever risks hitting Excel's
1,048,576-row limit):

- **`lta_train_od_historical_by_month.xlsx`** — the full dataset
- **`lta_train_od_EW1_by_month.xlsx`** — filtered to rows where station
  `EW1` (Pasir Ris) is the origin or destination

Both are committed to `main` and also uploaded as a workflow run artifact
(`lta-train-od-reports`) on every run that produces new data.

## The Two Workflows

### 1. Manual Fetch (`fetch-lta-data-manual.yml`)

Trigger it yourself whenever you want a fresh pull:

1. Go to **Actions** tab → **"LTA Data - Manual Fetch"**
2. Click **Run workflow**

It always fetches the last 3 published months (checking a 4th month as a
boundary confirmation, so requesting up to 4 months back), rebuilds both
workbooks, and commits + uploads them — regardless of whether the data
already exists locally.

### 2. Monthly Auto Fetch (`fetch-lta-data-monthly.yml`)

Runs on a schedule: **daily at 01:00 UTC from the 11th to the 20th of each
month** (LTA publishes the previous month's data by the 10th, so this window
gives it a day's buffer and 10 days of retry room). Each run:

1. Computes the target month (the most recently completed calendar month)
2. If that month's sheet already exists in the committed workbook, **exits
   immediately with no API calls** — this is what makes it safe to run daily
   without burning through the API quota once the month's data is in
3. Otherwise, fetches fresh data. If the new month still isn't published
   yet, the run **fails on purpose** (a visible red run) so it's obvious a
   retry is pending — the next day's scheduled run will try again
4. If the new month **is** available, rebuilds both workbooks and commits

You can also trigger it manually (workflow_dispatch) to test the logic
without waiting for the schedule.

## Setup Steps

### 1. Add Your LTA API Key as a Secret

1. Go to your repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `LTA_API_KEY`, Value: your API key
4. Click **Add secret**

### 2. Enable the workflows

Go to the **Actions** tab and enable workflows if prompted. Both workflow
files are picked up automatically once on `main`.

## ⚠️ Network Access Requirement

This sandboxed development environment's outbound proxy blocks
`datamall2.mytransport.sg` entirely, so the script can't be tested from
here. GitHub-hosted Actions runners are **not** behind that same proxy and
do reach the API fine (confirmed in testing) — so both workflows work
as-is once the secret is set.

## Manual Local Usage

On any machine with real internet access:

```bash
pip install -r requirements.txt

python3 fetch_lta_data.py "<YOUR_LTA_API_KEY>" "lta_train_od_historical.csv" 4
python3 build_reports.py lta_train_od_historical.csv lta_train_od_historical_by_month.xlsx
python3 build_reports.py lta_train_od_historical.csv lta_train_od_EW1_by_month.xlsx EW1
```

`fetch_lta_data.py` arguments (all optional, shown with defaults): API key,
output CSV filename (default `lta_train_od_historical.csv`), months to look
back (default `4`).

`build_reports.py` arguments: input CSV, output xlsx, optional station code
to filter by (omit for all stations).

## Troubleshooting

**"No historical data could be retrieved for any month in range"**
- Network access to `datamall2.mytransport.sg` is blocked from wherever you're running this — try a different network.
- Verify the API key is valid.

**"API rate limit / quota exceeded"**
- The LTA DataMall API key has a request quota. Repeated testing can exhaust it.
- The script stops immediately on this error and saves whatever it already collected; wait a while and try again.
- Both `fetch_lta_data.py` and `monthly_pipeline.py`'s idempotency check keep normal usage well within quota — the monthly workflow makes zero API calls once a month's data is already committed.

**Some months are missing from the output**
- Expected — LTA only publishes a rolling ~3-month window. The script logs which months it found data for.

**Monthly workflow shows a red/failed run**
- Expected when the new month isn't published yet (still before/around the 10th, or LTA is running late that month). It will retry automatically the next day within the 11th–20th window.
