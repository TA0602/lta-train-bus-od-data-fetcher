# LTA Train Historical Data Setup Guide

This guide explains how this repo fetches Singapore LTA train
Origin-Destination (OD) data from the `PV/ODTrain` DataMall API and
publishes it as Excel workbooks — committed to the repo, uploaded as
workflow artifacts, and (once configured) emailed to you as a zip.

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
confirmed empirically too (older months return 404).

## Files

- **`fetch_lta_data.py`** — fetches and merges historical OD train data into a CSV
- **`build_reports.py`** — converts a CSV into a multi-sheet Excel workbook (one sheet per month), optionally filtered to one station code
- **`pipeline_common.py`** — shared naming convention + "what's already covered" detection
- **`manual_pipeline.py`** — orchestrator for the on-demand workflow (always fetches + writes new files)
- **`monthly_pipeline.py`** — orchestrator for the scheduled workflow (idempotent, quota-aware)
- **`requirements.txt`** — Python dependencies (`requests`, `openpyxl`)
- **`.github/workflows/`** — the two workflows described below

## Output Files & Naming Convention

Every successful run (manual or scheduled) writes **two new files** into
the **`data/`** folder — it never overwrites a previous run's output:

```
data/lta_train_od_full_<start:YYYY-MM>_<end:YYYY-MM>_<run:YYYYMMDDThhmmssZ>.xlsx
data/lta_train_od_EW1_<start:YYYY-MM>_<end:YYYY-MM>_<run:YYYYMMDDThhmmssZ>.xlsx
```

For example: `data/lta_train_od_full_2026-06_2026-08_20260911T044637Z.xlsx`

- `start`/`end` are the actual months of data contained in the file (so
  filenames sort chronologically as plain text)
- the trailing run timestamp makes every run's output unique
- `full` = all stations; `EW1` = filtered to rows where station `EW1` is
  the origin or destination
- each workbook has **one sheet per month**, so no sheet risks exceeding
  Excel's 1,048,576-row limit

Each run also zips both files together (**`zip -9`**, max compression, into
one `.zip` — no other archive format) for the artifact/email attachment.

## The Two Workflows

### 1. Manual Fetch (`fetch-lta-data-manual.yml`)

Trigger it yourself whenever you want a fresh pull:

1. Go to **Actions** tab → **"LTA Data - Manual Fetch"**
2. Click **Run workflow**

Always fetches the last 3 published months (checking a 4th month as a
boundary confirmation), builds two new dated files, zips them, uploads the
artifact, commits to `main`, and emails the zip (once email is configured
— see below) — regardless of whether this data was already fetched before.

### 2. Monthly Auto Fetch (`fetch-lta-data-monthly.yml`)

Runs on a schedule: **daily at 01:00 UTC from the 11th to the 20th of each
month** (LTA publishes the previous month's data by the 10th, so this gives
a day's buffer and 10 days of retry room). Each run:

1. Computes the target month (the most recently completed calendar month)
2. If the newest `data/lta_train_od_full_*.xlsx` file's end-month already
   covers the target, **exits immediately with no API calls** — this is
   what makes daily retries safe without burning through the API quota
3. Otherwise, fetches fresh data. If the new month still isn't published,
   the run **fails on purpose** (a visible red run) — the next day's
   scheduled run retries
4. If the new month **is** available: builds two new dated files, zips,
   uploads, commits, and emails

You can also trigger it manually (`workflow_dispatch`) to test the logic
without waiting for the schedule.

## Setup Steps

### 1. Add Your LTA API Key

1. Go to your repo → **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret** → Name: `LTA_API_KEY`, Value: your API key

### 2. (Optional) Set Up Email Delivery

Both workflows check for email configuration and **skip the email step
silently** if it's incomplete — everything else (commit, artifact) still
works without this. To enable email, add these secrets:

| Secret | Example |
|---|---|
| `SMTP_SERVER` | `smtp.gmail.com`, `smtp.office365.com`, or your org's SMTP relay |
| `SMTP_PORT` | `587` (optional — defaults to 587 if unset) |
| `SMTP_USERNAME` | the mailbox/account used to authenticate |
| `SMTP_PASSWORD` | an app password (not your regular login password, for providers like Gmail/Office365) |
| `NOTIFY_EMAIL_TO` | the recipient address |

Email is sent via [`dawidd6/action-send-mail`](https://github.com/dawidd6/action-send-mail).

**⚠️ Size caveat:** the zipped attachment can be large — the full-dataset
workbook alone is roughly 90MB, since it's already XML/zip-compressed
internally and doesn't shrink much further. Most mail providers cap
attachments around 20–25MB, so this WILL likely be rejected by your mail
server as an attachment. If that happens, options are: filter to a smaller
subset before emailing, only email the small EW1 file, or switch the email
body to a link to the GitHub file/artifact instead of an attachment (ask
if you want this changed).

### 3. Enable the workflows

Go to the **Actions** tab and enable workflows if prompted.

## ⚠️ Network Access Requirement

This sandboxed development environment's outbound proxy blocks
`datamall2.mytransport.sg` entirely, so the script can't be tested from
here. GitHub-hosted Actions runners are **not** behind that same proxy and
do reach the API fine (confirmed in testing) — so both workflows work
as-is once `LTA_API_KEY` is set.

## Manual Local Usage

On any machine with real internet access:

```bash
pip install -r requirements.txt

# On-demand fetch, same as the manual workflow
python3 manual_pipeline.py "<YOUR_LTA_API_KEY>" 4
```

This writes the two dated files into `data/`. Or run the pieces individually:

```bash
python3 fetch_lta_data.py "<YOUR_LTA_API_KEY>" "lta_train_od_historical.csv" 4
python3 build_reports.py lta_train_od_historical.csv some_output.xlsx        # all stations
python3 build_reports.py lta_train_od_historical.csv some_output_ew1.xlsx EW1 # station filter
```

## Troubleshooting

**"No historical data could be retrieved for any month in range"**
- Network access to `datamall2.mytransport.sg` is blocked from wherever you're running this — try a different network.
- Verify the API key is valid.

**"API rate limit / quota exceeded"**
- The LTA DataMall API key has a request quota. Repeated testing can exhaust it.
- The script stops immediately on this error and saves whatever it already collected; wait a while and try again.
- `monthly_pipeline.py`'s idempotency check keeps normal usage well within quota — it makes zero API calls once a month's data is already committed.

**Some months are missing from the output**
- Expected — LTA only publishes a rolling ~3-month window. The script logs which months it found data for.

**Monthly workflow shows a red/failed run**
- Expected when the new month isn't published yet. It retries automatically the next day within the 11th–20th window.

**Email step didn't send anything**
- Check the "Check email configuration" step's log — it prints which secrets are missing. Also check the size caveat above; a mail-server rejection due to attachment size won't necessarily show as a workflow failure.
