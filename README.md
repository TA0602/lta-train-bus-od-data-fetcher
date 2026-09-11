# LTA Train & Bus OD Data Fetcher

Fetches Origin-Destination (OD) passenger volume data from Singapore's
[LTA DataMall](https://datamall.lta.gov.sg/) — both the `PV/ODTrain` API
(train stations) and the `PV/ODBus` API (bus stops) — and publishes each
as one Excel workbook per month, committed to `data/`, uploaded as workflow
artifacts, and (once configured) emailed to you as download links.

## What it does (train)

The `PV/ODTrain` endpoint doesn't return data rows directly — each call
(for a given `Date=YYYYMM`) returns a link to a ZIP file containing that
month's CSV of trip counts between stations. The pipeline queries the last
few months, downloads and extracts each available ZIP, and builds **one
workbook per month** — a run covering three months writes three full
workbooks and three EW1 workbooks, not one of each holding three sheets:

```
data/lta_train_od_full_<YYYY-MM>_<run-timestamp>.xlsx   — all stations
data/lta_train_od_EW1_<YYYY-MM>_<run-timestamp>.xlsx    — station EW1 only
```

Every run stamps its own timestamp, so a run never overwrites a previous
run's files. Within a month's file the data is normally a single sheet; a
month large enough to exceed Excel's 1,048,576-row per-sheet limit
continues onto `<month> (2)`, `<month> (3)`, ...

Two GitHub Actions workflows keep this up to date — see
**[LTA_DATA_SETUP.md](LTA_DATA_SETUP.md)** for the full explanation:

- **Manual Fetch** — run on demand, always re-pulls the last 3-4 months and writes new files
- **Monthly Auto Fetch** — runs daily from the 11th to the last day of each month, skips
  API calls once that month's data is already covered, and retries daily
  until LTA publishes it

Every successful run also emails an HTML message with direct download
links to every file it produced, once SMTP secrets are configured (optional — see
setup guide; the files themselves are too large to attach directly).

## What it does (bus)

The same pattern is mirrored for Singapore's `PV/ODBus` API (Passenger
Volume by Origin Destination Bus Stops — same CSV schema as the train
endpoint, but `ORIGIN_PT_CODE`/`DESTINATION_PT_CODE` are bus stop codes):

```
data/lta_bus_od_77009_<YYYY-MM>_<run-timestamp>.xlsx   — bus stop 77009 only
```

Same one-file-per-month convention as train.

**There is deliberately no "full" (all bus stops) workbook.** Singapore has
far more bus stops than train stations, so the unfiltered dataset came out
at ~588MB for three months — past GitHub's hard 100MB per-file push limit
(a real run was rejected with `GH001`), and past Excel's own per-sheet row
limit. The bus pipeline only ever builds the filtered workbook.

- **`fetch_lta_bus_data.py`** / **`bus_pipeline_common.py`** /
  **`manual_bus_pipeline.py`** / **`monthly_bus_pipeline.py`** — bus
  equivalents of the train scripts above, filtered to bus stop 77009
  (the bus equivalent of the EW1 filter on the train side)
- **`.github/workflows/fetch-lta-bus-data-manual.yml`** /
  **`fetch-lta-bus-data-monthly.yml`** — same manual/monthly split as the
  train workflows (monthly runs at `01:01 UTC` instead of `01:00`, to
  avoid both hitting LTA's short-window rate limit at the same instant)

## ⚠️ Repository history was purged (2026-09-11)

All git history prior to this notice was rewritten to strip every data
file (all `.xlsx`/`.csv.gz` blobs over 100KB) from every commit — this
removed accumulated test data from repo development, shrinking `.git`
from ~427MB down to ~264KB. The `data/` folder is now empty; it's
repopulated by the next manual or scheduled workflow run.

This was a deliberate, one-time cleanup (via `git filter-repo` +
force-push), done because the workflow design never overwrites or
deletes old dated files — so without this, the old test-era files would
have stayed in history forever. **If you have an existing local clone
from before this date, it's now out of sync with `origin/main`'s
history — re-clone rather than pulling.** All source code (scripts,
workflows, docs) was preserved untouched; only accumulated binary data
files were removed. See `HANDOVER.md` for full project context.

## Files

Train:
- **`fetch_lta_train_data.py`** — fetches and merges historical OD train data into a CSV
- **`train_pipeline_common.py`** — naming convention + "what's already covered" detection
- **`manual_train_pipeline.py`** / **`monthly_train_pipeline.py`** — orchestrators for each workflow

Bus:
- **`fetch_lta_bus_data.py`** — fetches and merges historical OD bus data into a CSV
- **`bus_pipeline_common.py`** — naming convention + "what's already covered" detection
- **`manual_bus_pipeline.py`** / **`monthly_bus_pipeline.py`** — orchestrators for each workflow

Shared:
- **`build_reports.py`** — splits a CSV into one Excel workbook per month, optionally filtered by station/bus-stop code
- **`requirements.txt`** — Python dependencies (`requests`, `openpyxl`)
- **`.github/workflows/`** — the train and bus workflows described above,
  plus `resend-lta-train-email.yml` (re-sends the email for the most
  recently built train files without calling the API again)
- **`LTA_DATA_SETUP.md`** — full setup guide, workflow details, and troubleshooting

## Quick start

```bash
pip install -r requirements.txt

# Train
python3 manual_train_pipeline.py "<YOUR_LTA_API_KEY>" 4

# Bus
python3 manual_bus_pipeline.py "<YOUR_LTA_API_KEY>" 4
```

Writes one dated workbook per month into `data/`.

Get an API key from the [LTA DataMall Developer Portal](https://datamall.lta.gov.sg/content/datamall/en/request-for-api.html).

See **[LTA_DATA_SETUP.md](LTA_DATA_SETUP.md)** for the GitHub Actions
workflows, email setup, naming convention, and troubleshooting (including
API rate limits and LTA's documented 3-month data retention window).
