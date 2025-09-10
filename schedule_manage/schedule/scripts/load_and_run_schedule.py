"""
Script to create an Event, Soldiers (with constraints), a SchedulingRun, and then
execute the scheduling algorithm using the project's REST API.

Why this script: It mirrors the serializers and endpoints found in the repo so
payloads match exactly, avoiding mismatch bugs.
"""
from __future__ import annotations
import json
import os
from typing import Any, Dict, List

import requests

BASE_URL = os.environ.get("SCHED_API_BASE", "http://127.0.0.1:8000/api")
TOKEN = os.environ.get("SCHED_API_TOKEN")  # Optional DRF Token or Session cookie


def _auth_headers() -> Dict[str, str]:
    # Use token auth if provided; fall back to no auth (for local dev)
    headers = {"Content-Type": "application/json"}
    if TOKEN:
        headers["Authorization"] = f"Token {TOKEN}"
    return headers


def create_event(event_payload: Dict[str, Any]) -> Dict[str, Any]:
    r = requests.post(f"{BASE_URL}/events/", headers=_auth_headers(), json=event_payload, timeout=30)
    r.raise_for_status()
    return r.json()


def create_soldier(event_id: int, soldier_payload: Dict[str, Any]) -> Dict[str, Any]:
    # SoldierDetailSerializer expects event_id and supports constraints_data
    soldier_payload = {**soldier_payload, "event_id": event_id}
    r = requests.post(f"{BASE_URL}/soldiers/", headers=_auth_headers(), json=soldier_payload, timeout=30)
    r.raise_for_status()
    return r.json()


def create_scheduling_run(event_id: int, name: str, description: str | None, soldiers_ids: List[int] | None) -> Dict[str, Any]:
    payload = {"event_id": event_id, "name": name}
    if description:
        payload["description"] = description
    # Optional: if provided, run will include only these soldiers; otherwise Event.soldiers will be used
    if soldiers_ids:
        payload["soldiers_ids"] = soldiers_ids
    r = requests.post(f"{BASE_URL}/scheduling-runs/", headers=_auth_headers(), json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def execute_algorithm(run_id: int) -> Dict[str, Any]:
    r = requests.post(f"{BASE_URL}/scheduling-runs/{run_id}/execute_algorithm/", headers=_auth_headers(), timeout=60)
    r.raise_for_status()
    return r.json()


def load_payload(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main(payload_path: str):
    data = load_payload(payload_path)

    # 1) Create Event
    event_resp = create_event(data["event"])  # returns EventSerializer fields
    event_id = event_resp["id"]
    print("Created event:", event_resp)

    # 2) Create Soldiers
    soldier_ids: List[int] = []
    for s in data.get("soldiers", []):
        s_resp = create_soldier(event_id, s)  # SoldierDetailSerializer result
        soldier_ids.append(s_resp["id"])
    print(f"Created {len(soldier_ids)} soldiers: {soldier_ids}")

    # 3) Create SchedulingRun (optionally limit to specific soldiers)
    run_meta = data.get("scheduling_run", {})
    run_resp = create_scheduling_run(
        event_id=event_id,
        name=run_meta.get("name", "Auto Run"),
        description=run_meta.get("description"),
        soldiers_ids=soldier_ids,  # include all created soldiers explicitly
    )
    run_id = run_resp["id"]
    print("Created scheduling run:", run_resp)

    # 4) Execute algorithm
    exec_resp = execute_algorithm(run_id)
    print("Execute result:", exec_resp)

    # 5) Optional: fetch assignments in calendar format
    cal = requests.get(
        f"{BASE_URL}/assignments/calendar/",
        headers=_auth_headers(),
        params={"scheduling_run": run_id},
        timeout=30,
    )
    cal.raise_for_status()
    print("Calendar sample (first 3 days):", dict(list(cal.json().items())[:3]))


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python load_and_run_schedule.py <path_to_payload.json>")
        print("Defaulting to scripts/sample_schedule_payload.json")
        payload_path = os.path.join(os.path.dirname(__file__), "sample_schedule_payload.json")
    else:
        payload_path = sys.argv[1]
    main(payload_path)
