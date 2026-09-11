#!/usr/bin/env python3
"""
Shared helpers for the bus OD pipelines: naming convention, output folder,
and month-coverage detection. Mirrors pipeline_common.py (train), but for
the PV/ODBus dataset and without a station filter (bus stop codes don't
have a single obvious default the way EW1 does for train).

Naming convention (sorts chronologically as plain filenames, and never
overwrites a previous run's output):

    data/lta_bus_od_full_<start:YYYY-MM>_<end:YYYY-MM>_<run:YYYYMMDDThhmmssZ>.xlsx
"""

import csv
import glob
import os
import re
from datetime import datetime, timezone

from build_reports import build_workbook

DATA_DIR = "data"

FULL_PREFIX = "lta_bus_od_full"

_FILENAME_RE = re.compile(r"_(\d{4}-\d{2})_(\d{4}-\d{2})_\d{8}T\d{6}Z\.xlsx$")


def month_range(csv_path):
    """Return (earliest, latest) YEAR_MONTH values ('YYYY-MM') found in the CSV."""
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        idx = header.index("YEAR_MONTH")
        months = {row[idx] for row in reader}
    return min(months), max(months)


def run_timestamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def build_named_reports(csv_path, out_dir=DATA_DIR):
    """Build the full workbook with the naming convention above.

    Returns (full_path, start_month, end_month).
    """
    os.makedirs(out_dir, exist_ok=True)
    start, end = month_range(csv_path)
    ts = run_timestamp()

    full_path = os.path.join(out_dir, f"{FULL_PREFIX}_{start}_{end}_{ts}.xlsx")

    build_workbook(csv_path, full_path)

    return full_path, start, end


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
