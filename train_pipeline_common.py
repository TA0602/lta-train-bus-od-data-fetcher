#!/usr/bin/env python3
"""
Shared helpers: naming convention, output folder, and month-coverage
detection used by both the manual and scheduled pipelines.

Naming convention (sorts chronologically as plain filenames, and never
overwrites a previous run's output):

    data/lta_train_od_full_<start:YYYY-MM>_<end:YYYY-MM>_<run:YYYYMMDDThhmmssZ>.xlsx
    data/lta_train_od_EW1_<start:YYYY-MM>_<end:YYYY-MM>_<run:YYYYMMDDThhmmssZ>.xlsx
"""

import glob
import os
import re
from datetime import datetime, timezone

from build_reports import build_workbooks

DATA_DIR = "data"
STATION = "EW1"

FULL_PREFIX = "lta_train_od_full"
EW1_PREFIX = "lta_train_od_EW1"

_FILENAME_RE = re.compile(r"_(\d{4}-\d{2})_(\d{4}-\d{2})_\d{8}T\d{6}Z\.xlsx$")


def run_timestamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def build_named_reports(csv_path, start, end, out_dir=DATA_DIR):
    """Build the full + EW1-filtered workbooks with the naming convention above.

    `start`/`end` come from the fetch step, which already knows which months
    it wrote — deriving them here would mean another full scan of the CSV.

    Returns (full_path, ew1_path).
    """
    os.makedirs(out_dir, exist_ok=True)
    ts = run_timestamp()

    full_path = os.path.join(out_dir, f"{FULL_PREFIX}_{start}_{end}_{ts}.xlsx")
    ew1_path = os.path.join(out_dir, f"{EW1_PREFIX}_{start}_{end}_{ts}.xlsx")

    build_workbooks(csv_path, [(full_path, None), (ew1_path, STATION)])

    return full_path, ew1_path


def latest_end_month_covered(out_dir=DATA_DIR):
    """Most recent 'end' month among existing full-data files in out_dir, or None."""
    pattern = os.path.join(out_dir, f"{FULL_PREFIX}_*.xlsx")
    best = None
    for path in glob.glob(pattern):
        m = _FILENAME_RE.search(os.path.basename(path))
        if m:
            end = m.group(2)
            if best is None or end > best:
                best = end
    return best
