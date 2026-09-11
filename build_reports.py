#!/usr/bin/env python3
"""
Convert a fetched LTA OD CSV into multi-sheet Excel workbooks (one sheet
per YEAR_MONTH), optionally filtered to rows involving a specific point
code (a train station code like EW1, or a bus stop code like 77009).

Usage:
    python3 build_reports.py <input_csv> <output_xlsx> [point_code]

If point_code is given, only rows where ORIGIN_PT_CODE or
DESTINATION_PT_CODE exactly equals it are included.
"""

import csv
import sys
from openpyxl import Workbook

# Excel refuses to open a sheet with more rows than this. A month that
# exceeds it is continued onto "<month> (2)", "<month> (3)", ... rather than
# silently producing a workbook Excel truncates or rejects.
EXCEL_MAX_ROWS = 1_048_576
ROWS_PER_SHEET = EXCEL_MAX_ROWS - 1  # one row is spent on the header


def _append(job, header, month, row):
    if job["counts"].get(month, 0) % ROWS_PER_SHEET == 0:
        part = job["parts"].get(month, 0) + 1
        job["sheets"][month] = job["wb"].create_sheet(
            title=month if part == 1 else f"{month} ({part})"
        )
        job["sheets"][month].append(header)
        job["parts"][month] = part
    job["sheets"][month].append(row)
    job["counts"][month] = job["counts"].get(month, 0) + 1


def build_workbooks(input_csv, targets):
    """Build several workbooks from a single pass over input_csv.

    targets: iterable of (output_xlsx, point_code_or_None).
    """
    jobs = [
        {
            "path": path,
            "code": code,
            "wb": Workbook(write_only=True),
            "sheets": {},
            "counts": {},
            "parts": {},
            "matched": 0,
        }
        for path, code in targets
    ]

    with open(input_csv, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        month_idx = header.index("YEAR_MONTH")
        origin_idx = header.index("ORIGIN_PT_CODE")
        dest_idx = header.index("DESTINATION_PT_CODE")

        total = 0
        for row in reader:
            total += 1
            month = row[month_idx]
            origin = row[origin_idx]
            dest = row[dest_idx]
            for job in jobs:
                code = job["code"]
                if code is not None and origin != code and dest != code:
                    continue
                _append(job, header, month, row)
                job["matched"] += 1

    for job in jobs:
        if not job["sheets"]:
            # Nothing matched this filter. Emit a header-only sheet instead of
            # aborting: the other workbooks in this pass are already built, and
            # failing here would leave the run half-finished after all the
            # fetching is done.
            print(f"[{job['path']}] ⚠ no rows matched {job['code']!r} — writing an empty workbook")
            job["wb"].create_sheet(title="no matches").append(header)

        job["wb"].save(job["path"])

        label = f"code {job['code']}" if job["code"] else "all points"
        print(f"[{job['path']}] {label}: {job['matched']}/{total} rows across {len(job['counts'])} month(s)")
        for month, n in sorted(job["counts"].items()):
            parts = job["parts"][month]
            suffix = f" (split across {parts} sheets)" if parts > 1 else ""
            print(f"  {month}: {n} rows{suffix}")


def build_workbook(input_csv, output_xlsx, station=None):
    build_workbooks(input_csv, [(output_xlsx, station)])


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 build_reports.py <input_csv> <output_xlsx> [point_code]")
        sys.exit(1)

    build_workbook(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
