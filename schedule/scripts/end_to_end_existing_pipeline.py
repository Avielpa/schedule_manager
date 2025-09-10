#!/usr/bin/env python3
"""
End-to-end pipeline for the existing system's single JSON:
- Input JSON must contain: { employees: [...], settings: {...}, shifts?: [...] }
- We translate employees/settings to the stateless solver input, run the solver,
  and translate the output back into the existing system's "shifts" format.
- Output JSON: { employees, settings, shifts }  (employees/settings preserved, shifts replaced).

Why this structure:
- Keep solver entirely in-memory to avoid DB dependencies.
- Preserve original employees/settings untouched for round-trip traceability.
- Make names unique for the solver (if duplicates) while maintaining a reliable
  mapping back to employeeId when creating shifts.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Use the algorithm layer directly (same as the stateless management command)
# Ensure we can import the Django app package "schedule" when running as a script
import sys
from pathlib import Path as _Path
_THIS = _Path(__file__).resolve()
# project root: .../schedule_manager
_PROJECT_ROOT = _THIS.parents[2]
# app parent containing "schedule" package: .../schedule_manager/schedule_manage
_APP_PARENT = _PROJECT_ROOT / "schedule_manage"
if str(_APP_PARENT) not in sys.path:
    sys.path.insert(0, str(_APP_PARENT))

from schedule.algorithms.solver import SmartScheduleSoldiers
from schedule.algorithms.soldier import Soldier as AlgorithmSoldier


# ----------------------------- helpers -----------------------------

def _parse_date(d: Any) -> date:
    if isinstance(d, date):
        return d
    if isinstance(d, str):
        return date.fromisoformat(d)
    raise ValueError(f"Unsupported date value: {d!r}")


def _get_setting(settings: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    for k in keys:
        if k in settings and settings[k] not in (None, ""):
            return settings[k]
    return default


def _gen_shift_id(base_ms: int) -> str:
    # Unique but human-friendly id format similar to partner examples
    return f"shift{base_ms}-{uuid.uuid4().hex[:9]}"


@dataclass
class ScheduleConfig:
    start_date: date
    end_date: date
    min_required: int = 5
    base_days: int = 30
    home_days: int = 25
    max_base: int = 7
    max_home: int = 10
    min_block: int = 3


# ----------------------------- core pipeline -----------------------------

def build_schedule_config(settings: Dict[str, Any], shifts: List[Dict[str, Any]] | None,
                          override_start: str | None = None,
                          override_end: str | None = None,
                          override_min_required: int | None = None) -> ScheduleConfig:
    # Accept both camelCase and snake_case inputs for compatibility
    start = override_start or _get_setting(settings, ["startDate", "start_date"])  # required or derive
    end = override_end or _get_setting(settings, ["endDate", "end_date"])        # required or derive

    if not start or not end:
        # If settings lacks dates, derive from shifts if present
        if shifts:
            dates = [s.get("date") for s in shifts if s.get("date")]
            if not dates:
                raise SystemExit("No dates found in shifts to derive schedule window.")
            start = min(dates)
            end = max(dates)
        else:
            raise SystemExit("settings.startDate/endDate missing and no shifts to derive from.")

    start_date = _parse_date(start)
    end_date = _parse_date(end)

    # Optional knobs; fall back to sensible defaults aligned with the stateless command
    min_required = int(override_min_required or _get_setting(settings, ["minRequiredPerDay", "min_required_soldiers_per_day"], 5))
    base_days = int(_get_setting(settings, ["baseDaysTarget", "base_days_per_soldier"], 30))
    home_days = int(_get_setting(settings, ["homeDaysTarget", "home_days_per_soldier"], 25))
    max_base = int(_get_setting(settings, ["maxConsecutiveBaseDays", "max_consecutive_base_days"], 7))
    max_home = int(_get_setting(settings, ["maxConsecutiveHomeDays", "max_consecutive_home_days"], 10))
    min_block = int(_get_setting(settings, ["minBaseBlockDays", "min_base_block_days"], 3))

    return ScheduleConfig(
        start_date=start_date,
        end_date=end_date,
        min_required=min_required,
        base_days=base_days,
        home_days=home_days,
        max_base=max_base,
        max_home=max_home,
        min_block=min_block,
    )


def build_algo_soldiers(employees: List[Dict[str, Any]]) -> Tuple[List[AlgorithmSoldier], Dict[str, str]]:
    """
    Build solver soldiers and a stable mapping from the solver's output name → employeeId.
    If duplicate names exist, suffix the display name with the employee id to keep uniqueness.
    """
    algo_soldiers: List[AlgorithmSoldier] = []
    out_name_to_id: Dict[str, str] = {}

    # Track duplicates by name
    name_counts: Dict[str, int] = {}
    for e in employees:
        name = e.get("name") or ""
        emp_id = str(e.get("id"))
        name_counts[name] = name_counts.get(name, 0) + 1

    for idx, e in enumerate(employees, start=1):
        name = e.get("name") or f"Employee {idx:02d}"
        emp_id = str(e.get("id") or idx)

        base_name = name
        if name_counts.get(name, 0) > 1:
            # Ensure uniqueness in solver results while keeping a clear link back
            name = f"{base_name} [{emp_id}]"

        # Support either unavailableDays (existing) or unavailable_days
        unavailable = e.get("unavailableDays")
        if unavailable is None:
            unavailable = e.get("unavailable_days", [])
        # Normalize to ISO strings
        unavailable = [d if isinstance(d, str) else _parse_date(d).isoformat() for d in (unavailable or [])]

        algo_soldiers.append(
            AlgorithmSoldier(
                id=emp_id,
                name=name,
                unavailable_days=unavailable,
                is_exceptional_output=bool(e.get("is_exceptional_output", False)),
                is_weekend_only_soldier_flag=bool(e.get("is_weekend_only_soldier_flag", False)),
            )
        )
        out_name_to_id[name] = emp_id

    return algo_soldiers, out_name_to_id


def run_solver(cfg: ScheduleConfig, soldiers: List[AlgorithmSoldier]) -> Dict[str, Any]:
    scheduler = SmartScheduleSoldiers(
        soldiers=soldiers,
        start_date=cfg.start_date,
        end_date=cfg.end_date,
        default_base_days_target=cfg.base_days,
        default_home_days_target=cfg.home_days,
        max_consecutive_base_days=cfg.max_base,
        max_consecutive_home_days=cfg.max_home,
        min_base_block_days=cfg.min_block,
        min_required_soldiers_per_day=cfg.min_required,
    )
    solution_data, status_code = scheduler.solve()
    if not solution_data:
        raise SystemExit("Solver returned no data")
    # Keep status for potential debugging; not exposed in final payload.
    return solution_data


def solution_to_shifts(solution: Dict[str, Any], name_to_emp_id: Dict[str, str]) -> List[Dict[str, Any]]:
    base_ms = int(time.time() * 1000)
    shifts: List[Dict[str, Any]] = []

    # Iterate the soldier schedules and emit only Base days as shifts
    for soldier_name, soldier_schedule in solution.items():
        if soldier_name == "daily_soldiers_count":
            continue
        emp_id = name_to_emp_id.get(soldier_name)
        for day_assignment in soldier_schedule.get("schedule", []):
            if day_assignment.get("status") == "Base":
                date_iso = day_assignment.get("date")
                shift_obj: Dict[str, Any] = {"id": _gen_shift_id(base_ms), "date": date_iso}
                if emp_id:
                    shift_obj["employeeId"] = emp_id
                else:
                    # Should not happen due to explicit mapping; keep a safety valve
                    shift_obj["employeeName"] = soldier_name
                shifts.append(shift_obj)

    return shifts


# ----------------------------- CLI -----------------------------

def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="End-to-end: existing JSON -> solver -> existing JSON")
    parser.add_argument("input", type=Path, help="Path to existing system input JSON (employees, settings, shifts?)")
    parser.add_argument("--out", type=Path, default=None, help="Output JSON path; defaults to <input>.out.json")
    parser.add_argument("--start", type=str, default=None, help="Override settings.startDate (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, default=None, help="Override settings.endDate (YYYY-MM-DD)")
    parser.add_argument("--min-required", type=int, default=None, help="Override settings.minRequiredPerDay")

    args = parser.parse_args(argv)

    with args.input.open("r", encoding="utf-8") as f:
        data = json.load(f)

    employees = data.get("employees") or []
    settings = data.get("settings") or {}
    shifts_in = data.get("shifts") or []  # ignored; replaced with new allocation

    if not employees:
        raise SystemExit("Input must include 'employees' array")

    cfg = build_schedule_config(
        settings,
        shifts_in,
        override_start=args.start,
        override_end=args.end,
        override_min_required=args.min_required,
    )
    algo_soldiers, out_name_to_id = build_algo_soldiers(employees)
    solution = run_solver(cfg, algo_soldiers)
    shifts_out = solution_to_shifts(solution, out_name_to_id)

    # Preserve settings; ensure canonical fields exist for consumers expecting camelCase
    settings_out = dict(settings)
    settings_out.setdefault("startDate", cfg.start_date.isoformat())
    settings_out.setdefault("endDate", cfg.end_date.isoformat())
    settings_out.setdefault("minRequiredPerDay", cfg.min_required)

    out_payload = {
        "employees": employees,
        "settings": settings_out,
        "shifts": shifts_out,
    }

    out_path = args.out or args.input.with_suffix(".out.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(out_payload, f, ensure_ascii=False, indent=2)

    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
