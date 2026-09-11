#!/usr/bin/env python3
"""
Split a fetched LTA OD CSV into one Excel workbook per YEAR_MONTH,
optionally filtered to rows involving a specific point code (a train
station code like EW1, or a bus stop code like 77009).

One month per file — a run covering three months writes three workbooks,
not one workbook with three sheets.

Usage:
    python3 build_reports.py <input_csv> <output_prefix> [point_code]

writes <output_prefix>_<YYYY-MM>.xlsx for each month present.
"""

import csv
import sys
from openpyxl import Workbook

# Excel refuses to open a sheet with more rows than this. A month that
# exceeds it is continued onto "<month> (2)", "<month> (3)", ... within that
# month's own workbook, rather than silently producing a file Excel
# truncates or rejects.
EXCEL_MAX_ROWS = 1_048_576
ROWS_PER_SHEET = EXCEL_MAX_ROWS - 1  # one row is spent on the header


def _new_book(path, code):
    return {
        "path": path,
        "code": code,
        "wb": Workbook(write_only=True),
        "sheets": {},
        "counts": {},
        "parts": {},
        "matched": 0,
    }


def _append(book, header, month, row):
    if book["counts"].get(month, 0) % ROWS_PER_SHEET == 0:
        part = book["parts"].get(month, 0) + 1
        book["sheets"][month] = book["wb"].create_sheet(
            title=month if part == 1 else f"{month} ({part})"
        )
        book["sheets"][month].append(header)
        book["parts"][month] = part
    book["sheets"][month].append(row)
    book["counts"][month] = book["counts"].get(month, 0) + 1


def build_monthly_workbooks(input_csv, targets):
    """Split input_csv into one workbook per (target, month), in a single pass.

    targets: iterable of (point_code_or_None, path_for_month), where
             path_for_month(month) returns that month's output path.

    Returns one {month: path} dict per target, in the same order. A month
    with no matching rows simply gets no file.
    """
    targets = list(targets)
    books = [{} for _ in targets]
    results = [{} for _ in targets]

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
            for i, (code, path_for_month) in enumerate(targets):
                if code is not None and origin != code and dest != code:
                    continue
                book = books[i].get(month)
                if book is None:
                    book = _new_book(path_for_month(month), code)
                    books[i][month] = book
                _append(book, header, month, row)
                book["matched"] += 1

    for i, (code, _) in enumerate(targets):
        label = f"code {code}" if code else "all points"
        if not books[i]:
            print(f"⚠ {label}: no rows matched anywhere in {total} row(s) — no files written")
            continue
        for month in sorted(books[i]):
            book = books[i][month]
            book["wb"].save(book["path"])
            results[i][month] = book["path"]
            parts = book["parts"][month]
            suffix = f" across {parts} sheets" if parts > 1 else ""
            print(f"[{book['path']}] {label}, {month}: {book['matched']} rows{suffix}")

    return results


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 build_reports.py <input_csv> <output_prefix> [point_code]")
        sys.exit(1)

    prefix = sys.argv[2]
    code = sys.argv[3] if len(sys.argv) > 3 else None
    (by_month,) = build_monthly_workbooks(input_csv=sys.argv[1], targets=[(code, lambda m: f"{prefix}_{m}.xlsx")])
    sys.exit(0 if by_month else 1)
