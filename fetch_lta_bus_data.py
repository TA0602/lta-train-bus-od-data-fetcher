#!/usr/bin/env python3
"""
LTA OD Bus Historical Data Fetcher

The LTA DataMall PV/ODBus endpoint does not return data rows directly.
Each call returns a JSON object with a "Link" to a ZIP file containing a
CSV of origin-destination bus trip counts for one month. This script
queries the endpoint for a range of months (via the Date=YYYYMM param),
downloads each available ZIP, and streams the rows inside straight into
one combined CSV — never holding a whole month's data in memory, which
matters more here than for train: there are far more bus stops than train
stations, so a month of bus OD data is substantially larger.
"""

import csv
import io
import os
import sys
import tempfile
import time
import zipfile
from datetime import date

import requests

BASE_URL = "https://datamall2.mytransport.sg/ltaodataservice/PV/ODBus"

DOWNLOAD_CHUNK = 1 << 20
RETRY_ATTEMPTS = 3
REQUEST_SPACING = 1.5  # seconds between month requests; see QuotaExceeded below


class QuotaExceeded(Exception):
    pass


def get_download_link(api_key, yyyymm):
    """Return the ZIP link for `yyyymm`, or None if LTA has no file for it.

    Raises QuotaExceeded on throttling so the caller stops immediately rather
    than recording a throttled month as "not published yet", and lets real
    4xx errors (e.g. 401 from a bad key) propagate instead of disguising them
    as missing data.
    """
    headers = {"AccountKey": api_key, "accept": "application/json"}
    params = {"Date": yyyymm}

    last_error = None
    for attempt in range(RETRY_ATTEMPTS):
        if attempt:
            time.sleep(2**attempt)
        try:
            response = requests.get(BASE_URL, headers=headers, params=params, timeout=30)
        except requests.exceptions.RequestException as e:
            last_error = e
            continue

        # The gateway throttles with either a 429 or a 500 carrying a quota
        # fault; retrying either is pointless until the window resets.
        if response.status_code == 429 or "QuotaViolation" in response.text:
            raise QuotaExceeded(response.text[:300])
        if response.status_code == 404:
            return None
        if response.status_code >= 500:
            last_error = requests.exceptions.HTTPError(
                f"{response.status_code} from LTA: {response.text[:200]}"
            )
            continue

        response.raise_for_status()
        data = response.json()
        values = data.get("value", []) if isinstance(data, dict) else data
        return values[0].get("Link") if values else None

    raise last_error


def download_zip(link, dest_path):
    """Stream the ZIP at `link` to dest_path without buffering it in memory."""
    with requests.get(link, timeout=300, stream=True) as response:
        response.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK):
                f.write(chunk)


def iter_csv_members(zip_path):
    """Yield (header, row_iterator) for each CSV member of the ZIP."""
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if not name.lower().endswith(".csv"):
                continue
            with zf.open(name) as raw:
                reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8-sig"))
                header = next(reader, None)
                if header is not None:
                    yield header, reader


def previous_months(count):
    """Return `count` YYYYMM strings for the months preceding the current month."""
    today = date.today()
    year, month = today.year, today.month
    result = []
    for _ in range(count):
        month -= 1
        if month == 0:
            month = 12
            year -= 1
        result.append(f"{year}{month:02d}")
    return result


def fetch_all_historical(api_key, output_file="lta_bus_od_historical.csv", months_back=4):
    """Fetch the last `months_back` months, streaming them into one CSV.

    Returns the sorted YEAR_MONTH values ('YYYY-MM') actually written, so
    callers don't have to re-read the file to learn what it contains. An
    empty list means nothing could be retrieved.
    """
    header = None
    month_idx = None
    months_seen = set()
    total_rows = 0

    with open(output_file, "w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)

        for i, yyyymm in enumerate(previous_months(months_back)):
            print(f"Checking {yyyymm}...")

            if i > 0:
                time.sleep(REQUEST_SPACING)

            try:
                link = get_download_link(api_key, yyyymm)
            except QuotaExceeded as e:
                print(f"\n✗ API rate limit / quota exceeded: {e}")
                print(f"  Stopping here with {total_rows} row(s) from {len(months_seen)} month(s).")
                print("  Wait for the quota to reset and try again later.")
                break
            except requests.exceptions.RequestException as e:
                print(f"  Error checking {yyyymm}: {e}")
                continue

            if not link:
                print(f"  No data available for {yyyymm}")
                continue

            print("  Found data, downloading...")
            fd, zip_path = tempfile.mkstemp(suffix=".zip")
            os.close(fd)
            month_rows = 0
            try:
                download_zip(link, zip_path)
                for member_header, rows in iter_csv_members(zip_path):
                    if header is None:
                        header = member_header
                        month_idx = header.index("YEAR_MONTH")
                        writer.writerow(header)
                    elif member_header != header:
                        print(f"  ✗ Skipping {yyyymm}: columns differ from earlier months")
                        print(f"    expected {header}")
                        print(f"    got      {member_header}")
                        break
                    for row in rows:
                        writer.writerow(row)
                        months_seen.add(row[month_idx])
                        month_rows += 1
            except Exception as e:
                print(f"  Failed to download/extract {yyyymm}: {e}")
                continue
            finally:
                os.unlink(zip_path)

            total_rows += month_rows
            print(f"  Added {month_rows} rows (total: {total_rows})")

    if not months_seen:
        print("\n✗ No historical data could be retrieved for any month in range")
        return []

    months = sorted(months_seen)
    print(f"\n✓ Successfully saved {total_rows} rows across {len(months)} month(s) to {output_file}")
    print(f"  Months included: {', '.join(months)}")
    print(f"  Columns: {', '.join(header)}")
    return months


if __name__ == "__main__":
    # LTA only publishes a rolling window of recent months (the API docs say
    # "up to last three months" for ODBus, matching what the train endpoint
    # does empirically) — default to a small buffer instead of scanning far
    # back and wasting API quota on months that will never have data.
    if len(sys.argv) < 2:
        print("Usage: python3 fetch_lta_bus_data.py <api_key> [output_csv] [months_back]")
        sys.exit(2)

    api_key = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "lta_bus_od_historical.csv"
    months_back = int(sys.argv[3]) if len(sys.argv) > 3 else 4

    sys.exit(0 if fetch_all_historical(api_key, output_file, months_back) else 1)
