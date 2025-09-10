"""
Export assignments to a JSON file for a given SchedulingRun.

Why a management command: Exporting server-side avoids adding output paths or
file I/O to API endpoints and keeps the behavior deterministic and scriptable
for CI or ops tasks. We mirror the calendar structure used by the API to keep
consumers consistent between programmatic and human-initiated exports.
"""
from __future__ import annotations

import json
import os
from typing import Dict

from django.core.management.base import BaseCommand, CommandError

from schedule.models import Assignment, SchedulingRun


class Command(BaseCommand):
    help = "Export assignments of a scheduling run to JSON (calendar or flat)."

    def add_arguments(self, parser):
        parser.add_argument("run_id", type=int, help="SchedulingRun ID to export")
        parser.add_argument(
            "--format",
            choices=["calendar", "flat"],
            default="calendar",
            help="Output format: calendar (group by date) or flat list",
        )
        parser.add_argument(
            "--out",
            type=str,
            default=None,
            help="Output file path. If omitted, a file under schedule/exports is created.",
        )

    def handle(self, *args, **options):
        run_id = options["run_id"]
        fmt = options["format"]
        out_path = options["out"]

        try:
            run = SchedulingRun.objects.get(id=run_id)
        except SchedulingRun.DoesNotExist:
            raise CommandError(f"SchedulingRun {run_id} not found")

        qs = (
            Assignment.objects.select_related("soldier", "scheduling_run")
            .filter(scheduling_run_id=run_id)
            .order_by("assignment_date", "soldier__name")
        )

        # Default output path is derived to make repeated runs predictable and not
        # depend on the current working directory; the exports folder keeps artifacts tidy.
        if not out_path:
            export_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "exports")
            export_dir = os.path.abspath(export_dir)
            os.makedirs(export_dir, exist_ok=True)
            out_path = os.path.join(export_dir, f"scheduling_run_{run_id}_{fmt}.json")
        else:
            os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

        if fmt == "calendar":
            data: Dict[str, dict] = {}
            for a in qs:
                d = a.assignment_date.strftime("%Y-%m-%d")
                if d not in data:
                    # Keep same shape as AssignmentViewSet.calendar to avoid divergent clients
                    data[d] = {"on_base": [], "at_home": []}
                soldier_data = {"id": a.soldier.id, "name": a.soldier.name, "rank": a.soldier.rank}
                if a.is_on_base:
                    data[d]["on_base"].append(soldier_data)
                else:
                    data[d]["at_home"].append(soldier_data)
        else:
            data = [
                {
                    "assignment_date": a.assignment_date.strftime("%Y-%m-%d"),
                    "is_on_base": a.is_on_base,
                    "soldier": {
                        "id": a.soldier.id,
                        "name": a.soldier.name,
                        "rank": a.soldier.rank,
                    },
                    "scheduling_run": run_id,
                }
                for a in qs
            ]

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.stdout.write(self.style.SUCCESS(f"Exported {qs.count()} assignments to {out_path}"))
