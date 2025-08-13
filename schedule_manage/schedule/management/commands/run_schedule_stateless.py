"""
Run the scheduling function completely stateless (no DB I/O):

Why stateless: This lets you test and integrate the solver in pipelines where a
database is undesirable. The command takes JSON inputs (schedule + soldiers),
invokes the solver directly, and exports assignments as JSON, matching the
calendar shape used by the REST API to keep consumers unified.
"""
from __future__ import annotations

import json
import os
from datetime import date
from typing import Any, Dict, List

from django.core.management.base import BaseCommand, CommandError

# Use the algorithm layer directly to avoid importing models and touching the DB
from schedule.algorithms.solver import SmartScheduleSoldiers
from schedule.algorithms.soldier import Soldier as AlgorithmSoldier


def _parse_date(d: Any) -> date:
    if isinstance(d, date):
        return d
    if isinstance(d, str):
        return date.fromisoformat(d)
    raise ValueError(f"Unsupported date value: {d!r}")


class Command(BaseCommand):
    help = "Run solver stateless from JSON and export assignments (calendar or flat)."

    def add_arguments(self, parser):
        parser.add_argument(
            "json_path",
            type=str,
            help="Path to JSON input. Accepts either {event, soldiers} or {schedule, soldiers}.",
        )
        parser.add_argument(
            "--format",
            choices=["calendar", "flat"],
            default="calendar",
            help="Output format: 'calendar' (by date) or 'flat' list.",
        )
        parser.add_argument(
            "--out",
            type=str,
            default=None,
            help="Path to output JSON. Defaults to schedule/exports/stateless_<fmt>.json",
        )

    def handle(self, *args, **options):
        path: str = options["json_path"]
        fmt: str = options["format"]
        out_path: str | None = options["out"]

        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as e:
            raise CommandError(f"Failed to read JSON: {e}")

        # Accept either 'schedule' or 'event' for time window and parameters to
        # avoid forcing schema changes on existing clients.
        schedule = payload.get("schedule") or payload.get("event")
        soldiers_in = payload.get("soldiers") or []
        if not schedule or not soldiers_in:
            raise CommandError("JSON must include 'schedule' or 'event' and a 'soldiers' array")

        # Extract and normalize schedule parameters. Defaults mirror view fallbacks
        # to keep behavior consistent across entrypoints.
        start_date = _parse_date(schedule.get("start_date"))
        end_date = _parse_date(schedule.get("end_date"))
        min_required = int(schedule.get("min_required_soldiers_per_day", 5))
        base_days = int(schedule.get("base_days_per_soldier", 30))
        home_days = int(schedule.get("home_days_per_soldier", 25))
        max_base = int(schedule.get("max_consecutive_base_days", 7))
        max_home = int(schedule.get("max_consecutive_home_days", 10))
        min_block = int(schedule.get("min_base_block_days", 3))

        # Build algorithm soldiers. We accept either 'unavailable_days' directly or
        # a 'constraints_data' list for convenience when reusing API-shaped payloads.
        algo_soldiers: List[AlgorithmSoldier] = []
        for i, s in enumerate(soldiers_in, start=1):
            name = s.get("name") or f"Soldier {i:02d}"
            sid = s.get("id") or s.get("soldier_id") or i
            sid = str(sid)

            unavailable = s.get("unavailable_days")
            if unavailable is None and s.get("constraints_data"):
                unavailable = [c.get("constraint_date") for c in s["constraints_data"] if c.get("constraint_date")]
            if unavailable is None:
                unavailable = []
            # Normalize to ISO strings since the algorithm expects strings
            unavailable = [d if isinstance(d, str) else _parse_date(d).isoformat() for d in unavailable]

            algo_soldiers.append(
                AlgorithmSoldier(
                    id=sid,
                    name=name,
                    unavailable_days=unavailable,
                    is_exceptional_output=bool(s.get("is_exceptional_output", False)),
                    is_weekend_only_soldier_flag=bool(s.get("is_weekend_only_soldier_flag", False)),
                )
            )

        scheduler = SmartScheduleSoldiers(
            soldiers=algo_soldiers,
            start_date=start_date,
            end_date=end_date,
            default_base_days_target=base_days,
            default_home_days_target=home_days,
            max_consecutive_base_days=max_base,
            max_consecutive_home_days=max_home,
            min_base_block_days=min_block,
            min_required_soldiers_per_day=min_required,
        )

        solution_data, status_code = scheduler.solve()
        if not solution_data:
            raise CommandError("Solver returned no data")

        # Prepare output path
        if not out_path:
            export_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "exports")
            export_dir = os.path.abspath(export_dir)
            os.makedirs(export_dir, exist_ok=True)
            out_path = os.path.join(export_dir, f"stateless_{fmt}.json")
        else:
            os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

        # Transform solution into requested format
        if fmt == "calendar":
            cal: Dict[str, dict] = {}
            for soldier_name, soldier_schedule in solution_data.items():
                if soldier_name == "daily_soldiers_count":
                    continue
                for day_assignment in soldier_schedule.get("schedule", []):
                    d = day_assignment.get("date")
                    status = day_assignment.get("status")
                    if not d:
                        continue
                    if d not in cal:
                        cal[d] = {"on_base": [], "at_home": []}
                    soldier_entry = {"name": soldier_name}
                    if status == "Base":
                        cal[d]["on_base"].append(soldier_entry)
                    else:
                        cal[d]["at_home"].append(soldier_entry)
            output = cal
        else:
            flat: List[dict] = []
            for soldier_name, soldier_schedule in solution_data.items():
                if soldier_name == "daily_soldiers_count":
                    continue
                for day_assignment in soldier_schedule.get("schedule", []):
                    flat.append(
                        {
                            "assignment_date": day_assignment.get("date"),
                            "is_on_base": day_assignment.get("status") == "Base",
                            "soldier": {"name": soldier_name},
                        }
                    )
            output = flat

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        self.stdout.write(self.style.SUCCESS(f"Stateless schedule exported to {out_path} (status={status_code})"))
