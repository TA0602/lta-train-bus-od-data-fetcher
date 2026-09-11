#!/usr/bin/env python3
"""
LTA OD Train Historical Data Fetcher

The LTA DataMall PV/ODTrain endpoint does not return data rows directly.
Each call returns a JSON object with a "Link" to a ZIP file containing a
CSV of origin-destination train trip counts for one month. This script
queries the endpoint for a range of months (via the Date=YYYYMM param),
downloads each available ZIP, extracts the CSV, and merges everything
into one combined CSV file.
"""

import requests
import zipfile
import io
import csv
import sys
from datetime import date

BASE_URL = "https://datamall2.mytransport.sg/ltaodataservice/PV/ODTrain"


def get_download_link(api_key, yyyymm, debug=False):
    """Query the API for a given month and return the ZIP download link, or None."""
    headers = {"AccountKey": api_key, "accept": "application/json"}
    params = {"Date": yyyymm}
    response = requests.get(BASE_URL, headers=headers, params=params, timeout=30)
    if debug and not response.ok:
        print(f"    [debug] status={response.status_code} body={response.text[:500]!r}")
    response.raise_for_status()
    data = response.json()
    values = data.get("value", []) if isinstance(data, dict) else data
    if not values:
        return None
    return values[0].get("Link")


def download_and_extract_rows(link):
    """Download the ZIP at `link` and return (fieldnames, rows) from the CSV inside."""
    response = requests.get(link, timeout=120)
    response.raise_for_status()

    fieldnames = None
    rows = []
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        for name in zf.namelist():
            if not name.lower().endswith(".csv"):
                continue
            with zf.open(name) as raw:
                text_stream = io.TextIOWrapper(raw, encoding="utf-8-sig")
                reader = csv.DictReader(text_stream)
                if fieldnames is None:
                    fieldnames = reader.fieldnames
                rows.extend(reader)
    return fieldnames, rows


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


def fetch_all_historical(api_key, output_file="lta_train_od_historical.csv", months_back=24):
    """
    Fetch OD train data for each of the last `months_back` months (skipping
    months with no data available) and save the combined result to CSV.
    """
    all_rows = []
    fieldnames = None
    months_found = []

    for i, yyyymm in enumerate(previous_months(months_back)):
        print(f"Checking {yyyymm}...")
        try:
            link = get_download_link(api_key, yyyymm, debug=(i < 3))
        except requests.exceptions.HTTPError as e:
            print(f"  No data / error for {yyyymm}: {e}")
            continue
        except requests.exceptions.RequestException as e:
            print(f"  Network error for {yyyymm}: {e}")
            continue

        if not link:
            print(f"  No data available for {yyyymm}")
            continue

        print(f"  Found data, downloading...")
        try:
            fnames, rows = download_and_extract_rows(link)
        except Exception as e:
            print(f"  Failed to download/extract {yyyymm}: {e}")
            continue

        if not rows:
            print(f"  ZIP for {yyyymm} contained no rows")
            continue

        if fieldnames is None:
            fieldnames = fnames

        for row in rows:
            row["_SourceMonth"] = yyyymm
        all_rows.extend(rows)
        months_found.append(yyyymm)
        print(f"  Added {len(rows)} rows (total: {len(all_rows)})")

    if not all_rows:
        print("\n✗ No historical data could be retrieved for any month in range")
        return False

    out_fieldnames = list(fieldnames or []) + ["_SourceMonth"]
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n✓ Successfully saved {len(all_rows)} rows across {len(months_found)} month(s) to {output_file}")
    print(f"  Months included: {', '.join(months_found)}")
    print(f"  Columns: {', '.join(out_fieldnames)}")
    return True


if __name__ == "__main__":
    api_key = sys.argv[1] if len(sys.argv) > 1 else "***REMOVED***"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "lta_train_od_historical.csv"
    months_back = int(sys.argv[3]) if len(sys.argv) > 3 else 24

    success = fetch_all_historical(api_key, output_file, months_back)
    sys.exit(0 if success else 1)
