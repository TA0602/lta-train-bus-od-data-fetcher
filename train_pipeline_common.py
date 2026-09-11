#!/usr/bin/env python3
"""
Shared helpers: naming convention, output folder, and month-coverage
detection used by both the manual and scheduled train pipelines.

One file per month — a run covering three months writes three full
workbooks and three EW1 workbooks, not one of each with three sheets:

    data/lta_train_od_full_<YYYY-MM>_<run:YYYYMMDDThhmmssZ>.xlsx
    data/lta_train_od_EW1_<YYYY-MM>_<run:YYYYMMDDThhmmssZ>.xlsx

(sorts chronologically as a plain filename, and never overwrites a previous
run's output — every run stamps its own timestamp)
"""

import glob
import os
import re
from datetime import datetime, timezone

from build_reports import build_monthly_workbooks

DATA_DIR = "data"
STATION = "EW1"

FULL_PREFIX = "lta_train_od_full"
EW1_PREFIX = "lta_train_od_EW1"

FILE_LIST = "report_files.txt"

_FILENAME_RE = re.compile(r"_(\d{4}-\d{2})_(\d{8}T\d{6}Z)\.xlsx$")


def run_timestamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def build_named_reports(csv_path, out_dir=DATA_DIR):
    """Build one full + one EW1 workbook for each month present in csv_path.

    Returns (full_by_month, ew1_by_month, ts), the first two being
    {YYYY-MM: path} dicts and ts the shared run timestamp.
    """
    os.makedirs(out_dir, exist_ok=True)
    ts = run_timestamp()

    full_by_month, ew1_by_month = build_monthly_workbooks(
        csv_path,
        [
            (None, lambda m: os.path.join(out_dir, f"{FULL_PREFIX}_{m}_{ts}.xlsx")),
            (STATION, lambda m: os.path.join(out_dir, f"{EW1_PREFIX}_{m}_{ts}.xlsx")),
        ],
    )

    return full_by_month, ew1_by_month, ts


def write_file_list(paths, list_path=FILE_LIST):
    """Record the files this run produced, for the workflow to add and link."""
    with open(list_path, "w", encoding="utf-8") as f:
        for path in paths:
            f.write(f"{path}\n")
    return list_path


def latest_end_month_covered(out_dir=DATA_DIR):
    """Most recent month among existing full-data files in out_dir, or None."""
    pattern = os.path.join(out_dir, f"{FULL_PREFIX}_*.xlsx")
    best = None
    for path in glob.glob(pattern):
        m = _FILENAME_RE.search(os.path.basename(path))
        if m:
            month = m.group(1)
            if best is None or month > best:
                best = month
    return best
