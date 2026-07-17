#!/usr/bin/env python3
"""Fail CI when a critical FaceGuard module falls below line coverage policy."""

import argparse
import json
from pathlib import Path
import sys

CRITICAL_MODULES = {
    "Recognition/enrollment orchestration": "backend/main.py",
    "Latest-frame camera pipeline": "backend/camera.py",
    "Employee, duplicate, temporary-access logic": "backend/db/employees_db.py",
    "Thread-safe database connection lifecycle": "backend/db/connection.py",
    "Recognition decision orchestration": "backend/faceguard/business_logic.py",
    "Face/liveness provider integration": "backend/faceguard/recognize.py",
    "JWT authentication": "backend/core/security.py",
    "LED/GPIO control": "backend/leds.py",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coverage-file", default="reports/coverage.json")
    parser.add_argument("--threshold", type=float, default=30.0)
    args = parser.parse_args()

    report_path = Path(args.coverage_file)
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"Unable to read coverage evidence {report_path}: {error}")
        return 2

    files = report.get("files", {})
    failures = []
    print("Critical module coverage:")
    for area, module in CRITICAL_MODULES.items():
        file_report = files.get(module)
        if file_report is None:
            failures.append(f"{module}: missing from coverage report")
            print(f"- {area}: MISSING ({module})")
            continue
        percent = float(file_report["summary"]["percent_covered"])
        result = "PASS" if percent >= args.threshold else "FAIL"
        print(f"- {area}: {percent:.2f}% ({result}) — {module}")
        if percent < args.threshold:
            failures.append(f"{module}: {percent:.2f}% is below {args.threshold:.2f}%")

    if failures:
        print("Critical coverage gate failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
