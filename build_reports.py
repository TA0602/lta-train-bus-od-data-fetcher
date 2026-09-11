#!/usr/bin/env python3
"""
Convert the fetched LTA OD train CSV into multi-sheet Excel workbooks
(one sheet per YEAR_MONTH), optionally filtered to rows involving a
specific station code.

Usage:
    python3 build_reports.py <input_csv> <output_xlsx> [station_code]

If station_code is given, only rows where ORIGIN_PT_CODE or
DESTINATION_PT_CODE exactly equals it are included.
"""

import csv
import sys
from openpyxl import Workbook


def build_workbook(input_csv, output_xlsx, station=None):
    wb = Workbook(write_only=True)
    sheets = {}
    counts = {}

    with open(input_csv, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        month_idx = header.index("YEAR_MONTH")
        origin_idx = header.index("ORIGIN_PT_CODE")
        dest_idx = header.index("DESTINATION_PT_CODE")

        total = 0
        matched = 0
        for row in reader:
            total += 1
            if station is not None and row[origin_idx] != station and row[dest_idx] != station:
                continue
            matched += 1
            month = row[month_idx]
            if month not in sheets:
                ws = wb.create_sheet(title=month)
                ws.append(header)
                sheets[month] = ws
                counts[month] = 0
            sheets[month].append(row)
            counts[month] += 1

    if not sheets:
        raise SystemExit(f"No rows matched (station={station!r}) — nothing to write.")

    wb.save(output_xlsx)

    label = f"station {station}" if station else "all stations"
    print(f"[{output_xlsx}] {label}: {matched}/{total} rows across {len(sheets)} month(s)")
    for month, n in sorted(counts.items()):
        print(f"  {month}: {n} rows")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 build_reports.py <input_csv> <output_xlsx> [station_code]")
        sys.exit(1)

    input_csv = sys.argv[1]
    output_xlsx = sys.argv[2]
    station = sys.argv[3] if len(sys.argv) > 3 else None

    build_workbook(input_csv, output_xlsx, station)
