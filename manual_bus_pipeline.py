#!/usr/bin/env python3
"""
Orchestrator for the on-demand bus OD workflow: always fetches fresh data
and always writes a new, uniquely-named file (never overwrites a prior
run's output).
"""

import os
import sys

from fetch_lta_bus_data import fetch_all_historical
from bus_pipeline_common import build_named_reports

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

    success = fetch_all_historical(api_key, CSV_TMP, months_back=months_back)
    if not success:
        print("Fetch failed — no data retrieved.")
        sys.exit(1)

    full_path, station_path, start, end = build_named_reports(CSV_TMP)
    print(f"Built {full_path} and {station_path} covering {start}..{end}.")

    set_output("full_path", full_path)
    set_output("station_path", station_path)
    set_output("start", start)
    set_output("end", end)


if __name__ == "__main__":
    main()
