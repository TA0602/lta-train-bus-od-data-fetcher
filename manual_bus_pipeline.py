#!/usr/bin/env python3
"""
Orchestrator for the on-demand bus OD workflow: always fetches fresh data
and always writes new, uniquely-named files (never overwrites a prior
run's output). Each month fetched becomes its own workbook.
"""

import os
import sys

from fetch_lta_bus_data import fetch_all_historical
from bus_pipeline_common import build_named_reports, write_file_list

CSV_TMP = "lta_bus_od_historical.csv"


def set_output(name, value):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a") as f:
            f.write(f"{name}={value}\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 manual_bus_pipeline.py <api_key> [months_back]")
        sys.exit(2)

    api_key = sys.argv[1]
    months_back = int(sys.argv[2]) if len(sys.argv) > 2 else 4

    months = fetch_all_historical(api_key, CSV_TMP, months_back=months_back)
    if not months:
        print("Fetch failed — no data retrieved.")
        sys.exit(1)

    station_by_month, ts = build_named_reports(CSV_TMP)

    paths = [station_by_month[m] for m in sorted(station_by_month)]
    if not paths:
        print("Fetch succeeded but no rows involved the configured bus stop — nothing to publish.")
        sys.exit(1)

    write_file_list(paths)
    print(f"Built {len(paths)} file(s): {', '.join(sorted(station_by_month))}")

    set_output("ts", ts)
    set_output("count", len(station_by_month))
    set_output("start", months[0])
    set_output("end", months[-1])


if __name__ == "__main__":
    main()
