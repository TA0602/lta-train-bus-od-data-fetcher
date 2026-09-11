#!/usr/bin/env python3
"""
Shared helpers for the bus OD pipelines: naming convention, output folder,
and month-coverage detection. Mirrors train_pipeline_common.py, but for the
PV/ODBus dataset and filtered to bus stop 77009.

One file per month — a run covering three months writes three workbooks,
not one with three sheets:

    data/lta_bus_od_77009_<YYYY-MM>_<run:YYYYMMDDThhmmssZ>.xlsx

Unlike the train side there is deliberately no "full" (all bus stops)
workbook. Singapore has far more bus stops than train stations, so the
unfiltered dataset came out at ~588MB for three months — past GitHub's hard
100MB per-file push limit, and past Excel's own per-sheet row limit. Only
the filtered workbook is produced and committed.
"""

import glob
import os
import re
from datetime import datetime, timezone

from build_reports import build_monthly_workbooks

DATA_DIR = "data"
STATION = "77009"

STATION_PREFIX = "lta_bus_od_77009"

FILE_LIST = "report_files.txt"

_FILENAME_RE = re.compile(r"_(\d{4}-\d{2})_(\d{8}T\d{6}Z)\.xlsx$")


def run_timestamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def build_named_reports(csv_path, out_dir=DATA_DIR):
    """Build one bus-stop-filtered workbook for each month present in csv_path.

    Returns (station_by_month, ts) — a {YYYY-MM: path} dict and the shared
    run timestamp.
    """
    os.makedirs(out_dir, exist_ok=True)
    ts = run_timestamp()

    (station_by_month,) = build_monthly_workbooks(
        csv_path,
        [(STATION, lambda m: os.path.join(out_dir, f"{STATION_PREFIX}_{m}_{ts}.xlsx"))],
    )

    return station_by_month, ts


def write_file_list(paths, list_path=FILE_LIST):
    """Record the files this run produced, for the workflow to add and link."""
    with open(list_path, "w", encoding="utf-8") as f:
        for path in paths:
            f.write(f"{path}\n")
    return list_path


def latest_end_month_covered(out_dir=DATA_DIR):
    """Most recent month among existing bus files in out_dir, or None."""
    pattern = os.path.join(out_dir, f"{STATION_PREFIX}_*.xlsx")
    best = None
    for path in glob.glob(pattern):
        m = _FILENAME_RE.search(os.path.basename(path))
        if m:
            month = m.group(1)
            if best is None or month > best:
                best = month
    return best
