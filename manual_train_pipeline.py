#!/usr/bin/env python3
"""
Orchestrator for the on-demand workflow: always fetches fresh data and
always writes new, uniquely-named files (never overwrites a prior run's
output).
"""

import os
import sys

from fetch_lta_train_data import fetch_all_historical
from train_pipeline_common import build_named_reports

CSV_TMP = "lta_train_od_historical.csv"


def set_output(name, value):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a") as f:
            f.write(f"{name}={value}\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 manual_train_pipeline.py <api_key> [months_back]")
        sys.exit(2)

    api_key = sys.argv[1]
    months_back = int(sys.argv[2]) if len(sys.argv) > 2 else 4

    success = fetch_all_historical(api_key, CSV_TMP, months_back=months_back)
    if not success:
        print("Fetch failed — no data retrieved.")
        sys.exit(1)

    full_path, ew1_path, start, end = build_named_reports(CSV_TMP)
    print(f"Built {full_path} and {ew1_path} covering {start}..{end}.")

    set_output("full_path", full_path)
    set_output("ew1_path", ew1_path)
    set_output("start", start)
    set_output("end", end)


if __name__ == "__main__":
    main()
