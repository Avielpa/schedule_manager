"""
Transform existing system JSON (employees) into the stateless solver's soldiers format.

Why this script: It decouples input formats by producing a stable soldiers block
the stateless runner understands. Optional CLI flags let you embed a 'schedule'
block to create a fully runnable payload in one step.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import date
from typing import Any, Dict, List


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Convert employees JSON to soldiers JSON")
    p.add_argument("input", help="Path to existing system JSON (with 'employees')")
    p.add_argument("--out", help="Output JSON path; defaults to <cwd>/soldiers_payload.json", default=None)

    # Optional schedule fields to produce a full stateless payload
    p.add_argument("--schedule-start", dest="schedule_start", help="Start date (YYYY-MM-DD)")
    p.add_argument("--schedule-end", dest="schedule_end", help="End date (YYYY-MM-DD)")
    p.add_argument("--min-required", dest="min_required", type=int, default=2, help="Min required per day")
    p.add_argument("--base-days", dest="base_days", type=int, default=30, help="Base days per soldier")
    p.add_argument("--home-days", dest="home_days", type=int, default=25, help="Home days per soldier")
    p.add_argument("--max-consecutive-base", dest="max_base", type=int, default=7, help="Max consecutive base days")
    p.add_argument("--max-consecutive-home", dest="max_home", type=int, default=10, help="Max consecutive home days")
    p.add_argument("--min-base-block", dest="min_block", type=int, default=3, help="Min base block days")
    return p.parse_args()


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _normalize_unavailable(days: Any) -> List[str]:
    # Keep dates as strings; the solver expects ISO strings at the interface
    if not days:
        return []
    out: List[str] = []
    for d in days:
        if isinstance(d, str):
            out.append(d)
        elif isinstance(d, (date,)):
            out.append(d.isoformat())
        else:
            out.append(str(d))
    return out


def convert_employees_to_soldiers(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    employees = data.get("employees") or []
    soldiers: List[Dict[str, Any]] = []
    for idx, emp in enumerate(employees, start=1):
        soldiers.append(
            {
                # Keep id if provided; solver accepts either 'id' or 'soldier_id'
                "id": str(emp.get("id") or idx),
                "name": emp.get("name") or f"Soldier {idx:02d}",
                "unavailable_days": _normalize_unavailable(emp.get("unavailableDays")),
                # color intentionally ignored to match request; flags default False
            }
        )
    return soldiers


def main() -> None:
    args = parse_args()
    src = _read_json(args.input)
    soldiers = convert_employees_to_soldiers(src)

    # If both schedule dates provided, emit full payload; otherwise emit soldiers only
    if args.schedule_start and args.schedule_end:
        payload: Dict[str, Any] = {
            "schedule": {
                "start_date": args.schedule_start,
                "end_date": args.schedule_end,
                "min_required_soldiers_per_day": args.min_required,
                "base_days_per_soldier": args.base_days,
                "home_days_per_soldier": args.home_days,
                "max_consecutive_base_days": args.max_base,
                "max_consecutive_home_days": args.max_home,
                "min_base_block_days": args.min_block,
            },
            "soldiers": soldiers,
        }
        default_out = os.path.join(os.getcwd(), "stateless_payload.json")
    else:
        payload = {"soldiers": soldiers}
        default_out = os.path.join(os.getcwd(), "soldiers_payload.json")

    out_path = args.out or default_out
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
