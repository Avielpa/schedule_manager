#!/usr/bin/env python3
"""
Translate stateless calendar output (algorithm result) into the existing system's
"shifts" JSON format using an employees file as the name→id mapping.

Why this design:
- We rely on employees.json (name↔id) instead of guessing IDs from names to avoid creating
  orphan references in the target system.
- We fail fast if a name from the calendar can't be mapped (optional --allow-unmapped),
  so data issues surface early rather than creating silent bad data.
- Shift IDs use a timestamp-based prefix + random suffix to be unique across runs while
  remaining compact and human-inspectable (mirrors example like "shift<ms>-<slug>").
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, List, Any


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_name_to_id(employees: List[Dict[str, Any]]) -> Dict[str, str]:
    # Normalize by exact name; avoid fuzzy matching to prevent accidental mis-maps.
    mapping: Dict[str, str] = {}
    for e in employees:
        name = e.get("name")
        emp_id = e.get("id")
        if not name or not emp_id:
            continue
        if name in mapping and mapping[name] != emp_id:
            # Detect duplicates to prevent ambiguous outputs.
            raise ValueError(f"Duplicate employee name with different IDs: {name!r}")
        mapping[name] = emp_id
    return mapping


def gen_shift_id(base_ms: int) -> str:
    # Use stable base per run + short random hex to keep it unique and readable.
    suffix = uuid.uuid4().hex[:9]
    return f"shift{base_ms}-{suffix}"


def translate(calendar: Dict[str, Any], name_to_id: Dict[str, str], allow_unmapped: bool) -> Dict[str, Any]:
    base_ms = int(time.time() * 1000)
    shifts: List[Dict[str, Any]] = []
    unmapped: List[str] = []

    # Sort dates for deterministic output for review/testing.
    for date in sorted(calendar.keys()):
        day = calendar[date] or {}
        on_base = day.get("on_base") or []
        # Only emit shifts for "on_base" allocations; "at_home" isn't a shift in the partner's model.
        for entry in on_base:
            name = (entry or {}).get("name")
            if not name:
                continue
            emp_id = name_to_id.get(name)
            if not emp_id:
                if not allow_unmapped:
                    unmapped.append(name)
                    continue
                # When permitted, pass through the human name to maintain traceability downstream.
                shift = {
                    "id": gen_shift_id(base_ms),
                    "date": date,
                    "employeeName": name,
                }
            else:
                shift = {
                    "id": gen_shift_id(base_ms),
                    "employeeId": emp_id,
                    "date": date,
                }
            shifts.append(shift)

    if unmapped:
        # Fail after collecting all offenders for clearer action, instead of failing on first.
        names = ", ".join(sorted(set(unmapped)))
        raise SystemExit(
            f"Unmapped names found in calendar (no matching employee.id). "
            f"Fix input_example.json or use --allow-unmapped to include 'employeeName': {names}"
        )

    return {"shifts": shifts}


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Convert stateless calendar to existing shifts JSON")
    parser.add_argument(
        "--calendar",
        type=Path,
        default=Path("schedule_manage/exports/stateless_calendar.json"),
        help="Path to stateless calendar JSON (default: schedule_manage/exports/stateless_calendar.json)",
    )
    parser.add_argument(
        "--employees",
        type=Path,
        default=Path("translate_example/input_example.json"),
        help="Path to employees JSON containing 'employees' array with id/name (default: translate_example/input_example.json)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("translate_example/schedule_from_stateless.json"),
        help="Output path for the existing system shifts JSON (default: translate_example/schedule_from_stateless.json)",
    )
    parser.add_argument(
        "--allow-unmapped",
        action="store_true",
        help="Allow names not present in employees; emits 'employeeName' instead of aborting.",
    )
    args = parser.parse_args(argv)

    calendar_obj = load_json(args.calendar)
    # calendar_obj expected to be {"YYYY-MM-DD": {"on_base": [{"name": ...}], "at_home": [...]}, ...}

    employees_obj = load_json(args.employees)
    if isinstance(employees_obj, dict) and "employees" in employees_obj:
        employees = employees_obj["employees"]
    elif isinstance(employees_obj, list):
        employees = employees_obj
    else:
        raise SystemExit("employees file must be a list or have an 'employees' key")

    name_to_id = build_name_to_id(employees)

    output = translate(calendar_obj, name_to_id, allow_unmapped=args.allow_unmapped)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
