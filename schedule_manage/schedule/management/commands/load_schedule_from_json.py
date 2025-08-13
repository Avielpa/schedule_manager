"""
Management command: load schedule inputs from a JSON file, create Event/Soldiers/
SchedulingRun, then execute the algorithm and persist assignments.

Why this command: Avoids HTTP and DRF setup by using the same model flow the
view uses, ensuring identical behavior while being easy to run locally.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any, Dict, List

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from schedule.models import (
    Event,
    Soldier,
    SoldierConstraint,
    SchedulingRun,
    Assignment,
)

# Import scheduling algorithm components once and fail early if missing to
# avoid partial writes or confusing runtime errors deep in execution.
try:
    from schedule.algorithms.solver import SmartScheduleSoldiers
    from schedule.algorithms.soldier import Soldier as AlgorithmSoldier
except Exception as e:  # pragma: no cover - environment specific
    SmartScheduleSoldiers = None
    AlgorithmSoldier = None
    _import_error = e
else:
    _import_error = None


class Command(BaseCommand):
    help = "Load schedule inputs from JSON, create records, and run the solver."

    def add_arguments(self, parser):
        parser.add_argument(
            "json_path",
            type=str,
            help="Path to JSON payload (see scripts/sample_schedule_payload.json)",
        )
        parser.add_argument(
            "--use-existing-event",
            action="store_true",
            help="If an event with same name and dates exists, reuse it instead of creating a new one.",
        )

    def handle(self, *args, **options):
        if _import_error is not None:
            raise CommandError(
                f"Scheduling components not available: {_import_error}. Ensure algorithm package is importable."
            )

        path = options["json_path"]
        reuse_event = options["use_existing_event"]

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise CommandError(f"Failed to read JSON: {e}")

        event_data: Dict[str, Any] = data.get("event") or {}
        soldiers_data: List[Dict[str, Any]] = data.get("soldiers") or []
        run_meta: Dict[str, Any] = data.get("scheduling_run") or {}

        if not event_data:
            raise CommandError("Missing 'event' object in JSON")

        # Create or reuse Event. We avoid DRF serializers here to keep CLI light
        # and because validation rules are simple and enforced by DB constraints.
        with transaction.atomic():
            event = None
            if reuse_event:
                event = Event.objects.filter(
                    name=event_data.get("name"),
                    start_date=event_data.get("start_date"),
                    end_date=event_data.get("end_date"),
                ).first()

            if event is None:
                # Parse date strings to date objects to avoid passing strings downstream
                start_dt = event_data["start_date"]
                end_dt = event_data["end_date"]
                if isinstance(start_dt, str):
                    start_dt = date.fromisoformat(start_dt)
                if isinstance(end_dt, str):
                    end_dt = date.fromisoformat(end_dt)

                event = Event.objects.create(
                    name=event_data["name"],
                    description=event_data.get("description"),
                    event_type=event_data.get("event_type", "OTHER"),
                    start_date=start_dt,
                    end_date=end_dt,
                    min_required_soldiers_per_day=event_data.get("min_required_soldiers_per_day", 10),
                    base_days_per_soldier=event_data.get("base_days_per_soldier"),
                    home_days_per_soldier=event_data.get("home_days_per_soldier"),
                    max_consecutive_base_days=event_data.get("max_consecutive_base_days", 7),
                    max_consecutive_home_days=event_data.get("max_consecutive_home_days", 10),
                    min_base_block_days=event_data.get("min_base_block_days", 3),
                )

            self.stdout.write(self.style.SUCCESS(f"Event ready: id={event.id} name={event.name}"))

            # Create Soldiers and optional constraints. We add event FK explicitly
            # to mirror the API contract used by SoldierDetailSerializer.
            soldier_ids: List[int] = []
            for s in soldiers_data:
                soldier = Soldier.objects.create(
                    event=event,
                    name=s["name"],
                    soldier_id=s.get("soldier_id"),
                    rank=s.get("rank", "PRIVATE"),
                    is_exceptional_output=s.get("is_exceptional_output", False),
                    is_weekend_only_soldier_flag=s.get("is_weekend_only_soldier_flag", False),
                )

                for c in s.get("constraints_data", []) or []:
                    cd = c["constraint_date"]
                    if isinstance(cd, str):
                        cd = date.fromisoformat(cd)
                    SoldierConstraint.objects.create(
                        soldier=soldier,
                        constraint_date=cd,
                        description=c.get("description"),
                        constraint_type=c.get("constraint_type", "PERSONAL"),
                    )

                soldier_ids.append(soldier.id)

            if soldier_ids:
                self.stdout.write(self.style.SUCCESS(f"Created {len(soldier_ids)} soldiers"))

            # Create SchedulingRun; by setting soldiers explicitly we control
            # get_target_soldiers() to use this subset; if omitted, event.soldiers is used.
            run = SchedulingRun.objects.create(
                event=event,
                name=run_meta.get("name", f"Schedule for {event.name}"),
                description=run_meta.get("description"),
            )
            if soldier_ids:
                run.soldiers.set(soldier_ids)

        # Execute algorithm mirroring the view logic to ensure parity.
        if run.status == "IN_PROGRESS":
            raise CommandError("Run already in progress")

        run.assignments.all().delete()
        run.status = "IN_PROGRESS"
        run.save(update_fields=["status"])

        try:
            qs = run.get_target_soldiers()
            if not qs.exists():
                run.status = "FAILURE"
                run.solution_details = "No soldiers available for scheduling"
                run.save(update_fields=["status", "solution_details"])
                raise CommandError("No soldiers available for scheduling")

            # Keep type hints simple to avoid issues when AlgorithmSoldier is a runtime import
            algo_soldiers: List = []
            for s in qs:
                # The view uses ISO date strings for unavailable days to keep the
                # algorithm I/O decoupled from Django's date type.
                constraint_strings = [
                    d.isoformat() if hasattr(d, "isoformat") else str(d)
                    for d in s.constraints.values_list("constraint_date", flat=True)
                ]
                algo_soldiers.append(
                    AlgorithmSoldier(
                        id=str(s.id),
                        name=s.name,
                        unavailable_days=constraint_strings,
                        is_exceptional_output=s.is_exceptional_output,
                        is_weekend_only_soldier_flag=s.is_weekend_only_soldier_flag,
                    )
                )

            event = run.event
            base_days = event.base_days_per_soldier or 30
            home_days = event.home_days_per_soldier or 25

            algorithm = SmartScheduleSoldiers(
                soldiers=algo_soldiers,
                start_date=event.start_date,
                end_date=event.end_date,
                default_base_days_target=base_days,
                default_home_days_target=home_days,
                max_consecutive_base_days=event.max_consecutive_base_days,
                max_consecutive_home_days=event.max_consecutive_home_days,
                min_base_block_days=event.min_base_block_days,
                min_required_soldiers_per_day=event.min_required_soldiers_per_day,
            )

            solution_data, status_code = algorithm.solve()

            if solution_data and status_code in [1, 2]:  # OPTIMAL or FEASIBLE
                assignments: List[Assignment] = []
                for soldier_name, soldier_schedule in solution_data.items():
                    if soldier_name == "daily_soldiers_count":
                        continue
                    try:
                        soldier = qs.get(name=soldier_name)
                    except Soldier.DoesNotExist:
                        self.stderr.write(f"Soldier {soldier_name} not found; skipping")
                        continue
                    for day_assignment in soldier_schedule["schedule"]:
                        assignment_date = date.fromisoformat(day_assignment["date"])
                        is_on_base = day_assignment["status"] == "Base"
                        assignments.append(
                            Assignment(
                                scheduling_run=run,
                                soldier=soldier,
                                assignment_date=assignment_date,
                                is_on_base=is_on_base,
                            )
                        )

                Assignment.objects.bulk_create(assignments)
                run.status = "SUCCESS"
                run.solution_details = f"Successfully created {len(assignments)} assignments"
                run.save(update_fields=["status", "solution_details"])
                self.stdout.write(self.style.SUCCESS(run.solution_details))
            else:
                run.status = "NO_SOLUTION"
                run.solution_details = "No feasible solution found"
                run.save(update_fields=["status", "solution_details"])
                raise CommandError("No feasible solution found")

        except Exception as e:
            # Keep error surfaced and store failure state to aid debugging.
            run.status = "FAILURE"
            run.solution_details = f"Algorithm failed: {e}"
            run.save(update_fields=["status", "solution_details"])
            raise

        self.stdout.write(self.style.SUCCESS(f"Run complete: id={run.id} status={run.status}"))
