#!/usr/bin/env python3
"""
Shared helpers for the bus OD pipelines: naming convention, output folder,
and month-coverage detection. Mirrors train_pipeline_common.py, but for the
PV/ODBus dataset and filtered to bus stop 77009.

Unlike the train side there is deliberately no "full" (all bus stops)
workbook. Singapore has far more bus stops than train stations, so the
unfiltered dataset came out at ~588MB for three months — past GitHub's hard
100MB per-file push limit, and past Excel's own per-sheet row limit. Only
the filtered workbook is produced and committed:

    data/lta_bus_od_77009_<start:YYYY-MM>_<end:YYYY-MM>_<run:YYYYMMDDThhmmssZ>.xlsx

(sorts chronologically as a plain filename, and never overwrites a previous
run's output)
"""

import glob
import os
import re
from datetime import datetime, timezone

from build_reports import build_workbooks

DATA_DIR = "data"
STATION = "77009"

STATION_PREFIX = "lta_bus_od_77009"

_FILENAME_RE = re.compile(r"_(\d{4}-\d{2})_(\d{4}-\d{2})_\d{8}T\d{6}Z\.xlsx$")


def run_timestamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def build_named_reports(csv_path, start, end, out_dir=DATA_DIR):
    """Build the bus-stop-filtered workbook with the naming convention above.

    `start`/`end` come from the fetch step, which already knows which months
    it wrote — deriving them here would mean another full scan of the CSV.

    Returns station_path.
    """
    os.makedirs(out_dir, exist_ok=True)
    ts = run_timestamp()

    station_path = os.path.join(out_dir, f"{STATION_PREFIX}_{start}_{end}_{ts}.xlsx")

    build_workbooks(csv_path, [(station_path, STATION)])

    return station_path


def latest_end_month_covered(out_dir=DATA_DIR):
    """Most recent 'end' month among existing bus files in out_dir, or None."""
    pattern = os.path.join(out_dir, f"{STATION_PREFIX}_*.xlsx")
    best = None
    for path in glob.glob(pattern):
        m = _FILENAME_RE.search(os.path.basename(path))
        if m:
            end = m.group(2)
            if best is None or end > best:
                best = end
    return best
