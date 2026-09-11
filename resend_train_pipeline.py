#!/usr/bin/env python3
"""
Find the most recent run's train report files already committed in data/
and record them — used by the resend-email workflow to email existing data
without hitting the LTA API again.

Files are one-month-per-file and every file from a given run shares that
run's timestamp, so "the latest run" is simply the newest timestamp.
"""

import glob
import os
import re

from train_pipeline_common import DATA_DIR, FULL_PREFIX, EW1_PREFIX, write_file_list

_FILENAME_RE = re.compile(r"_(\d{4}-\d{2})_(\d{8}T\d{6}Z)\.xlsx$")


def set_output(name, value):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a") as f:
            f.write(f"{name}={value}\n")


def main():
    found = []
    for prefix in (FULL_PREFIX, EW1_PREFIX):
        for path in glob.glob(os.path.join(DATA_DIR, f"{prefix}_*.xlsx")):
            m = _FILENAME_RE.search(os.path.basename(path))
            if m:
                month, ts = m.groups()
                found.append((ts, month, path))

    if not found:
        print(f"No existing report files found in {DATA_DIR}/.")
        raise SystemExit(1)

    latest_ts = max(ts for ts, _, _ in found)
    batch = sorted(entry for entry in found if entry[0] == latest_ts)
    months = sorted({month for _, month, _ in batch})
    paths = [path for _, _, path in batch]

    write_file_list(paths)
    print(f"Using {len(paths)} file(s) from run {latest_ts} covering {', '.join(months)}:")
    for path in paths:
        print(f"  {path}")

    set_output("ts", latest_ts)
    set_output("count", len(months))
    set_output("start", months[0])
    set_output("end", months[-1])


if __name__ == "__main__":
    main()
