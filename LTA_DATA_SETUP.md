# LTA Train Historical Data Setup Guide

This guide explains how to fetch Singapore LTA train Origin-Destination (OD)
data from the `PV/ODTrain` DataMall API.

## How the API Actually Works

The `PV/ODTrain` endpoint does **not** return data rows directly. Each call
(with a `Date=YYYYMM` query parameter) returns a JSON object containing a
**link to a ZIP file** holding a CSV of OD trip counts for that month:

```json
{ "value": [ { "Link": "https://.../PVODTrain202401.zip" } ] }
```

`fetch_lta_data.py` queries a range of months, downloads each available ZIP,
extracts the CSV inside, tags each row with its source month, and merges
everything into one combined CSV file.

LTA typically only keeps a rolling window of recent months available (older
months return no link) — the script simply skips any month with no data, so
you'll end up with however many months are actually published, not
necessarily the full `months_back` you request.

## What's Included

- **fetch_lta_data.py** — fetches and merges historical OD train data into a CSV
- **requirements.txt** — Python dependencies (just `requests`; zip/csv handling uses the standard library)
- **.github/workflows/fetch-lta-data.yml** — optional GitHub Actions workflow (manual trigger)

## ⚠️ Network Access Requirement

Both this sandboxed environment's outbound proxy and this repository's
GitHub Actions runners are blocked by network policy from reaching
`datamall2.mytransport.sg`. You must run the script from a machine/network
that can actually reach the LTA DataMall API (e.g. your own laptop on a
normal internet connection). If you want to use the GitHub Actions workflow
instead, it will only work if your organization's Actions runners have
outbound access to that host.

## Manual Usage (recommended)

On a machine with real internet access:

```bash
pip install requests

python3 fetch_lta_data.py "<YOUR_LTA_API_KEY>" "lta_train_od_historical.csv" 24
```

Arguments (all optional, shown with defaults):
1. API key (`AccountKey`)
2. Output CSV filename (default `lta_train_od_historical.csv`)
3. Number of months to look back from today (default `24`)

Then commit the result if you want it in the repo:

```bash
git add lta_train_od_historical.csv
git commit -m "chore: add LTA historical train OD data"
git push origin main
```

## Optional: GitHub Actions Setup

### 1. Add Your LTA API Key as a Secret

1. Go to your repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `LTA_API_KEY`, Value: your API key
4. Click **Add secret**

### 2. Run the Workflow

1. Go to the **Actions** tab
2. Select **"Fetch LTA Train Historical Data"**
3. Click **Run workflow**

This only succeeds if the Actions runner has network access to the LTA API —
test the manual method first if you're unsure.

### 3. Download the Result

The dataset (all months combined) can easily be 100MB+, over GitHub's
per-file commit limit, so the workflow uploads it as a **workflow run
artifact** rather than only relying on a git commit:

1. Go to the workflow run's summary page (**Actions** tab → the run)
2. Scroll to **Artifacts** and download `lta-train-od-historical-data`
   (contains both the raw `.csv` and a `.csv.gz` compressed copy)

If the gzip-compressed file happens to be under 50MB, the workflow also
commits it straight to the repo as `lta_train_od_historical.csv.gz` — unzip
it locally with `gunzip lta_train_od_historical.csv.gz`.

## Converting to Excel

The output is CSV. To get an `.xlsx` file, open the CSV in Excel/Google
Sheets and save/export as `.xlsx`, or run a local conversion:

```bash
pip install pandas openpyxl
python3 -c "import pandas as pd; pd.read_csv('lta_train_od_historical.csv').to_excel('lta_train_od_historical.xlsx', index=False)"
```

## Troubleshooting

**"No historical data could be retrieved for any month in range"**
- Network access to `datamall2.mytransport.sg` is blocked from wherever you're running this — try a different network.
- Verify the API key is valid.

**"API rate limit / quota exceeded"**
- The LTA DataMall API key has a request quota. Repeated testing (including earlier broken versions of this script that hammered the endpoint) can exhaust it.
- Wait a while and try again later — the script now stops immediately on this error and saves whatever it already collected instead of wasting further requests.
- The script also waits 1.5s between month requests to avoid tripping this again.

**Some months are missing from the output**
- Expected — LTA only publishes a rolling window of recent months. The script logs which months it found data for.
