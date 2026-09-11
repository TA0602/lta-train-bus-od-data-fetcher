#!/usr/bin/env python3
"""
Orchestrator for the on-demand train workflow: always fetches fresh data
and always writes new, uniquely-named files (never overwrites a prior
run's output). Each month fetched becomes its own pair of workbooks.
"""

import os
import sys

from fetch_lta_train_data import fetch_all_historical
from train_pipeline_common import build_named_reports, write_file_list

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

    months = fetch_all_historical(api_key, CSV_TMP, months_back=months_back)
    if not months:
        print("Fetch failed — no data retrieved.")
        sys.exit(1)

    full_by_month, ew1_by_month, ts = build_named_reports(CSV_TMP)

    paths = [full_by_month[m] for m in sorted(full_by_month)]
    paths += [ew1_by_month[m] for m in sorted(ew1_by_month)]
    if not paths:
        print("Fetch succeeded but no workbooks were produced.")
        sys.exit(1)

    write_file_list(paths)
    print(f"Built {len(paths)} file(s) across {len(full_by_month)} month(s): {', '.join(sorted(full_by_month))}")

    set_output("ts", ts)
    set_output("count", len(full_by_month))
    set_output("start", months[0])
    set_output("end", months[-1])


if __name__ == "__main__":
    main()
