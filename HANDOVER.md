# Handover Notes — LTA Train OD Data Fetcher

Written 2026-09-11 for whoever (human or Claude Code session) picks this
project up next. Read this before making changes — several non-obvious
things were discovered the hard way.

## What this project is

Fetches Singapore LTA train Origin-Destination (OD) passenger volume data
from the LTA DataMall `PV/ODTrain` API and publishes it as multi-sheet
Excel workbooks (one sheet per month, to stay under Excel's 1,048,576-row
limit), committed to `data/`, uploaded as workflow artifacts, and emailed
as download links.

Repo: `TA0602/lta-train-od-data-fetcher` (renamed from `TA0602/Hi` partway
through development — old bookmarks/clones using the `Hi` name still
resolve via GitHub's redirect, but update them).

## Current state (as of this handover)

- **Git history was just purged** (see README's notice) — `.git` went
  from ~427MB to ~264KB by stripping all blobs >100KB from every commit.
  `data/` is now **empty**. This is expected; the next workflow run
  repopulates it.
- Two GitHub Actions workflows are live and tested end-to-end on real
  data: `fetch-lta-data-manual.yml` and `fetch-lta-data-monthly.yml`,
  plus a utility `resend-email.yml`.
- **Required secret**: `LTA_API_KEY` must be set (Settings → Secrets and
  variables → Actions) for any workflow to fetch data.
- **Optional secrets for email**: `SMTP_SERVER`, `SMTP_PORT` (defaults
  587), `SMTP_USERNAME`, `SMTP_PASSWORD`, `NOTIFY_EMAIL_TO` (comma-separate
  for multiple recipients). Both fetch workflows silently skip the email
  step if these aren't fully set — nothing breaks without them. As of
  this handover the user had these configured and email was confirmed
  working (HTML body renders correctly with `html_body` input — see
  gotcha below).

## Architecture

```
fetch_lta_data.py       — talks to the LTA API, downloads/extracts ZIPs, writes a flat CSV
build_reports.py        — CSV -> multi-sheet xlsx (one sheet per YEAR_MONTH), optional station filter
pipeline_common.py      — naming convention + "what month range is already covered in data/" detection
manual_pipeline.py      — orchestrator: always fetch + always write new dated files (no coverage check)
monthly_pipeline.py     — orchestrator: check coverage first, skip if already have target month, else fetch ONLY that 1 month
resend_pipeline.py      — finds latest existing data/ file pair, no API call — used to resend email / test email formatting cheaply
```

Naming convention (sorts chronologically as plain text, never overwritten):
```
data/lta_train_od_full_<start:YYYY-MM>_<end:YYYY-MM>_<run:YYYYMMDDThhmmssZ>.xlsx
data/lta_train_od_EW1_<start:YYYY-MM>_<end:YYYY-MM>_<run:YYYYMMDDThhmmssZ>.xlsx
```

### The two real workflows

- **Manual** (`workflow_dispatch` only): always calls `fetch_all_historical(months_back=4)`
  — fetches whatever's currently published (typically last 3 months) regardless
  of what's already in `data/`. No idempotency check by design — user explicitly
  wants "give me a fresh pull" behavior here.
- **Monthly** (cron `0 1 11-31 * *` = daily 01:00 UTC / 09:00 SGT, 11th
  through last day of month, `workflow_dispatch` also works for testing):
  checks `pipeline_common.latest_end_month_covered()` against the target
  month (most recently completed calendar month) first. If already
  covered, exits immediately with **zero API calls**. Otherwise fetches
  **only that 1 month** (`months_back=1`) — critical, see gotcha below.
  If the month still isn't published, the run fails on purpose so the
  next day's scheduled run retries.

## Hard-won gotchas — don't rediscover these

1. **`PV/ODTrain` is not a paginated row API.** Each call (with
   `Date=YYYYMM`) returns `{"value": [{"Link": "https://.../zip"}]}` — a
   link to a ZIP containing that month's CSV, not data rows directly. The
   very first implementation wrongly used `$skip` pagination against a
   single call and got "1 record" every time.

2. **LTA's real rate limit is a short-window burst limit, NOT the
   documented 10M/day ToS threshold.** The actual API returns
   `{"fault":{"faultstring":"Rate limit quota violation...","errorcode":"policies.ratelimit.QuotaViolation"}}`
   (an Apigee gateway throttle) after roughly 10-15 requests within a
   couple of minutes. This is why `fetch_lta_data.py` sleeps 1.5s between
   month requests, and why `monthly_pipeline.py` was changed to fetch
   only 1 month instead of re-fetching the whole 3-4 month window every
   run (that was wasting 2/3 of every monthly run's requests on months
   already fetched previously).

3. **LTA's actual data retention is ~3 months**, confirmed both
   empirically (older months 404) and in the official API User Guide PDF
   (section 2.5-2.8): "Request for files up to last three months."

4. **GitHub Actions runner has real internet access; this dev sandbox
   does not.** The sandbox's outbound proxy blocks `datamall2.mytransport.sg`
   and `datamall.lta.gov.sg` entirely. Don't waste time debugging "network
   errors" when testing scripts locally in a Claude Code sandbox — they'll
   only work when actually run via GitHub Actions (or a machine with real
   internet).

5. **`dawidd6/action-send-mail` has no `content_type` input.** Use
   `html_body:` directly, not `body:` + `content_type: text/html` — the
   latter silently gets ignored (logged as "unexpected input" warning)
   and sends literal HTML tags as plain text. Confirmed via a live send
   before being caught and fixed.

6. **Action version pins go stale fast — verify, don't guess.** Training
   knowledge said `actions/checkout@v4` / `setup-python@v5` were current;
   by the time this repo was built (Sep 2026) the real latest majors were
   `checkout@v7`, `setup-python@v7`, `upload-artifact@v7`,
   `dawidd6/action-send-mail@v21` — confirmed via `git ls-remote --tags`
   and checking each `action.yml`'s `runs: using:` field is `node24`
   before bumping. Bumping to a wrong "latest" version still shows the
   Node20 deprecation warning; verify empirically via a real workflow run
   before trusting a version bump fixed something.

7. **Excel's 1,048,576-row-per-sheet limit is real and silent.** A single
   flat CSV with 2.68M rows opened directly in Excel truncates mid-file
   with no obvious error to a casual user (June shows complete, July
   shows partial, August never loads) — this is why the whole
   multi-sheet-by-month design exists.

8. **This repo was renamed mid-project**: `TA0602/Hi` →
   `TA0602/lta-train-od-data-fetcher`. If `git remote -v` ever shows the
   old `Hi` URL, that's fine (GitHub redirects), but prefer updating it to
   avoid confusion: `git remote set-url origin https://github.com/TA0602/lta-train-od-data-fetcher.git`

9. **The old `claude/modest-cannon-qzr926` feature branch was deleted**
   (both locally and on GitHub) after confirming it was fully merged into
   `main` with no unique commits. `main` is the only branch now.

## Open items / things the next session might need to pick up

- The monthly workflow has only been validated via manual
  `workflow_dispatch` triggers and one real scheduled behavior wasn't
  yet observed (the actual cron fire hadn't been confirmed as of this
  handover — worth checking Actions run history for a `schedule`-triggered
  run once enough time has passed).
- No automated cleanup/retention policy exists for `data/` — by design,
  files accumulate forever. Growth math (see prior conversation): ~31MB/month
  on monthly-only cadence, which would take over a decade to threaten
  GitHub's 5GB soft repo-size guidance — not urgent, but the user was
  made aware and chose to purge test-era history rather than set up
  ongoing pruning. No automated pruning exists; if this becomes a real
  concern later, options discussed: Git LFS, periodic manual purges (same
  `git filter-repo` approach used here), or external storage.
- Email delivery links point to `raw.githubusercontent.com` URLs
  constructed from `${{ github.repository }}`/`${{ github.ref_name }}` —
  these will break if the repo is renamed/moved again without updating
  nothing needs to change in code (they're computed at runtime), but
  worth remembering if the repo moves again.
- No tests exist beyond live workflow runs against the real API. All
  validation so far has been "trigger the real workflow, read the logs."
