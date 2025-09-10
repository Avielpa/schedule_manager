# Scheduling integration flow (short)

This folder contains DB-free scripts that let you:
1) Convert the existing system JSON into the solver’s format
2) Run the scheduling function
3) Convert the solver output back to the existing “shifts” JSON

## 3-step flow
1) Convert employees → solver input (stateless payload)
   - Input example: `translate_example/input_example.json` (has `employees`)
   - Output example: `translate_example/from_employees_stateless_payload.json` (has `schedule` + `soldiers`)
   - Command:
     - python schedule/scripts/transform_employees_to_soldiers.py translate_example/input_example.json --schedule-start 2025-08-01 --schedule-end 2025-09-05 --min-required 3 --out translate_example/from_employees_stateless_payload.json

2) Run the scheduling function (stateless)
   - Produces calendar JSON at `schedule_manage/exports/stateless_calendar.json` unless `--out` is provided
   - Command:
     - python schedule_manage/manage.py run_schedule_stateless translate_example/from_employees_stateless_payload.json --format calendar --out schedule_manage/exports/stateless_calendar.json

3) Convert solver calendar → existing system “shifts”
   - Requires the employees file to map names→employeeId
   - Command:
     - python schedule/scripts/translate_stateless_to_existing.py --calendar schedule_manage/exports/stateless_calendar.json --employees translate_example/input_example.json --out translate_example/schedule_from_stateless.json
   - Tip: add `--allow-unmapped` to emit `employeeName` when no `employeeId` exists in the mapping.

## One-step alternative
Use a single command to do everything in one go (read `{employees, settings[, shifts?]}` → run solver → write `{employees, settings, shifts}`):
- python schedule/scripts/end_to_end_existing_pipeline.py /path/to/input.json --out /path/to/output.json
- If your input lacks dates in `settings`, override:
  - python schedule/scripts/end_to_end_existing_pipeline.py /path/to/input.json --start 2025-08-01 --end 2025-09-05 --min-required 3 --out /path/to/output.json

## Notes
- Only “on_base” entries become shifts; “at_home” isn’t a shift in the partner schema.
- Duplicate names are disambiguated for the solver by suffixing ` [employeeId]` so we can map back to the correct `employeeId`.
- Shift IDs are generated as `shift<timestamp>-<short-uuid>` for uniqueness and readability.
