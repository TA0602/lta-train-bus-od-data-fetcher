#!/usr/bin/env python3
"""
Find the most recently built full+EW1 report pair already committed in
data/ and output their paths — used by the resend-email workflow to email
existing data without hitting the LTA API again.
"""

import glob
import os
import re

from train_pipeline_common import DATA_DIR, FULL_PREFIX, EW1_PREFIX

_FILENAME_RE = re.compile(r"_(\d{4}-\d{2})_(\d{4}-\d{2})_(\d{8}T\d{6}Z)\.xlsx$")


def set_output(name, value):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a") as f:
            f.write(f"{name}={value}\n")


def main():
    pattern = os.path.join(DATA_DIR, f"{FULL_PREFIX}_*.xlsx")
    candidates = []
    for path in glob.glob(pattern):
        m = _FILENAME_RE.search(os.path.basename(path))
        if m:
            start, end, ts = m.groups()
            candidates.append((ts, start, end, path))

    if not candidates:
        print(f"No existing report files found matching {pattern}.")
        raise SystemExit(1)

    candidates.sort()
    ts, start, end, full_path = candidates[-1]
    ew1_path = os.path.join(DATA_DIR, f"{EW1_PREFIX}_{start}_{end}_{ts}.xlsx")

    if not os.path.exists(ew1_path):
        print(f"Expected matching EW1 file not found: {ew1_path}")
        raise SystemExit(1)

    print(f"Using existing files ({start}..{end}): {full_path}, {ew1_path}")
    set_output("full_path", full_path)
    set_output("ew1_path", ew1_path)
    set_output("start", start)
    set_output("end", end)


if __name__ == "__main__":
    main()
