#!/usr/bin/env python3
"""
Orchestrator for the scheduled monthly bus OD workflow.

LTA publishes each month's data by the 10th of the following month. This
script is meant to run daily from the 11th onward: it first checks whether
the just-published month is already covered by an existing dated file in
data/ (no wasted API calls if so), and only calls the LTA API when there's
actually new data to fetch. Sets GITHUB_OUTPUT `updated=true|false` (plus
file path when true) for the workflow to decide whether to zip/email/
commit, and exits non-zero when the new month isn't published yet so the
workflow's daily retry has something to act on.
"""

import os
import sys
from datetime import date

from fetch_lta_bus_data import fetch_all_historical
from bus_pipeline_common import (
    build_named_reports,
    latest_end_month_covered,
    write_file_list,
)

CSV_TMP = "lta_bus_od_historical.csv"


def target_month_dash():
    """The most recently completed calendar month, as 'YYYY-MM'."""
    today = date.today()
    year, month = today.year, today.month
    month -= 1
    if month == 0:
        month = 12
        year -= 1
    return f"{year}-{month:02d}"


def set_output(name, value):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a") as f:
            f.write(f"{name}={value}\n")


def main():
    api_key = sys.argv[1] if len(sys.argv) > 1 else None
    if not api_key:
        print("Usage: python3 monthly_bus_pipeline.py <api_key>")
        sys.exit(2)

    dash_month = target_month_dash()
    covered = latest_end_month_covered()

    if covered is not None and covered >= dash_month:
        print(f"Already have data through {covered} (target {dash_month}) — nothing to do.")
        set_output("updated", "false")
        sys.exit(0)

    print(f"Looking for newly published data for {dash_month}...")
    # Only fetch the one new target month — older months never change once
    # published and are already covered by a previous run's committed
    # file, so re-fetching them here would just waste API quota.
    months = fetch_all_historical(api_key, CSV_TMP, months_back=1)

    if not months:
        print(f"No data available yet for {dash_month}.")
        set_output("updated", "false")
        sys.exit(1)

    if dash_month not in months:
        print(f"Fetch succeeded but {dash_month} still isn't published (found: {months}).")
        set_output("updated", "false")
        sys.exit(1)

    station_by_month, ts = build_named_reports(CSV_TMP)

    paths = [station_by_month[m] for m in sorted(station_by_month)]
    if not paths:
        print("Fetch succeeded but no rows involved the configured bus stop — nothing to publish.")
        set_output("updated", "false")
        sys.exit(1)

    write_file_list(paths)
    print(f"Built {len(paths)} file(s) for {dash_month}.")

    set_output("updated", "true")
    set_output("ts", ts)
    set_output("count", len(station_by_month))
    set_output("start", months[0])
    set_output("end", months[-1])


if __name__ == "__main__":
    main()
