# JSON API Guide for Schedule Management System

## Overview

This guide demonstrates how to use the Schedule Management System API with JSON POST requests. All endpoints support full JSON request/response functionality with comprehensive validation and error handling.

## Base URL
```
http://localhost:8000/api/
```

## Authentication
Currently set to `AllowAny` for development. In production, you should configure proper authentication.

## Content Type
All POST/PUT/PATCH requests should use:
```
Content-Type: application/json
```

---

## 1. Events API

### Create Event
**Endpoint:** `POST /api/events/`

**Request Body:**
```json
{
  "name": "Training Exercise",
  "event_type": "TRAINING",
  "description": "Advanced military training",
  "start_date": "2025-02-01",
  "end_date": "2025-02-28",
  "min_required_soldiers_per_day": 8,
  "base_days_per_soldier": 14,
  "home_days_per_soldier": 13,
  "max_consecutive_base_days": 5,
  "max_consecutive_home_days": 8,
  "min_base_block_days": 2
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Training Exercise",
  "event_type": "TRAINING",
  "description": "Advanced military training",
  "start_date": "2025-02-01",
  "end_date": "2025-02-28",
  "min_required_soldiers_per_day": 8,
  "base_days_per_soldier": 14,
  "home_days_per_soldier": 13,
  "max_consecutive_base_days": 5,
  "max_consecutive_home_days": 8,
  "min_base_block_days": 2,
  "created_by": null,
  "created_by_username": null,
  "created_at": "2025-08-10T03:24:14.719808Z"
}
```

**Event Types:** `TRAINING`, `EXERCISE`, `HOLIDAY`, `MAINTENANCE`, `INSPECTION`, `CEREMONY`, `OTHER`

### List Events
**Endpoint:** `GET /api/events/`

**Query Parameters:**
- `event_type`: Filter by event type
- `start_date`: Filter events starting after this date
- `end_date`: Filter events ending before this date

---

## 2. Soldiers API

### Create Single Soldier
**Endpoint:** `POST /api/soldiers/`

**Request Body:**
```json
{
  "name": "John Doe",
  "soldier_id": "S001",
  "rank": "SERGEANT",
  "is_exceptional_output": true,
  "is_weekend_only_soldier_flag": false,
  "constraints_data": [
    {
      "constraint_date": "2025-02-15",
      "constraint_type": "PERSONAL",
      "description": "Personal leave"
    },
    {
      "constraint_date": "2025-02-20",
      "constraint_type": "MEDICAL",
      "description": "Medical appointment"
    }
  ]
}
```

**Response:**
```json
{
  "id": 7,
  "name": "John Doe",
  "soldier_id": "S001",
  "rank": "SERGEANT",
  "is_exceptional_output": true,
  "is_weekend_only_soldier_flag": false,
  "constraints": [
    {
      "id": 2,
      "soldier": 7,
      "soldier_name": "John Doe",
      "constraint_date": "2025-02-15",
      "description": "Personal leave",
      "constraint_type": "PERSONAL",
      "created_at": "2025-08-10T03:24:23.786471Z"
    },
    {
      "id": 3,
      "soldier": 7,
      "soldier_name": "John Doe",
      "constraint_date": "2025-02-20",
      "description": "Medical appointment",
      "constraint_type": "MEDICAL",
      "created_at": "2025-08-10T03:24:23.786471Z"
    }
  ],
  "created_at": "2025-08-10T03:24:23.778267Z"
}
```

**Ranks:** `PRIVATE`, `CORPORAL`, `SERGEANT`, `LIEUTENANT`, `CAPTAIN`, `MAJOR`, `COLONEL`, `GENERAL`, `CIVILIAN`

### Bulk Create Soldiers
**Endpoint:** `POST /api/soldiers/bulk_create/`

**Request Body:**
```json
[
  {
    "name": "Soldier 1",
    "soldier_id": "BULK001",
    "rank": "PRIVATE",
    "is_exceptional_output": false,
    "is_weekend_only_soldier_flag": false
  },
  {
    "name": "Soldier 2",
    "soldier_id": "BULK002",
    "rank": "CORPORAL",
    "is_exceptional_output": true,
    "is_weekend_only_soldier_flag": false,
    "constraints_data": [
      {
        "constraint_date": "2025-02-10",
        "constraint_type": "TRAINING",
        "description": "Course training"
      }
    ]
  }
]
```

**Response:**
```json
{
  "created_soldiers": [
    {
      "id": 8,
      "name": "Soldier 1",
      "soldier_id": "BULK001",
      "rank": "PRIVATE",
      "is_exceptional_output": false,
      "is_weekend_only_soldier_flag": false,
      "constraints": [],
      "created_at": "2025-08-10T03:24:35.945176Z"
    },
    {
      "id": 9,
      "name": "Soldier 2",
      "soldier_id": "BULK002",
      "rank": "CORPORAL",
      "is_exceptional_output": true,
      "is_weekend_only_soldier_flag": false,
      "constraints": [
        {
          "id": 4,
          "soldier": 9,
          "soldier_name": "Soldier 2",
          "constraint_date": "2025-02-10",
          "description": "Course training",
          "constraint_type": "TRAINING",
          "created_at": "2025-08-10T03:24:35.961070Z"
        }
      ],
      "created_at": "2025-08-10T03:24:35.952583Z"
    }
  ],
  "errors": [],
  "summary": {
    "total": 2,
    "created": 2,
    "failed": 0
  }
}
```

### List Soldiers
**Endpoint:** `GET /api/soldiers/`

**Query Parameters:**
- `rank`: Filter by rank
- `is_exceptional`: Filter exceptional soldiers (`true`/`false`)
- `is_weekend_only`: Filter weekend-only soldiers (`true`/`false`)

---

## 3. Soldier Constraints API

### Create Constraint
**Endpoint:** `POST /api/soldier-constraints/`

**Request Body:**
```json
{
  "soldier": 7,
  "constraint_date": "2025-02-25",
  "constraint_type": "FAMILY",
  "description": "Family event"
}
```

**Response:**
```json
{
  "id": 5,
  "soldier": 7,
  "soldier_name": "John Doe",
  "constraint_date": "2025-02-25",
  "description": "Family event",
  "constraint_type": "FAMILY",
  "created_at": "2025-08-10T03:24:43.127060Z"
}
```

**Constraint Types:** `PERSONAL`, `MEDICAL`, `TRAINING`, `FAMILY`, `OFFICIAL`, `OTHER`

### List Constraints
**Endpoint:** `GET /api/soldier-constraints/`

**Query Parameters:**
- `soldier`: Filter by soldier ID
- `constraint_type`: Filter by constraint type
- `start_date`: Filter constraints from this date
- `end_date`: Filter constraints until this date

---

## 4. Scheduling Runs API

### Create Scheduling Run
**Endpoint:** `POST /api/scheduling-runs/`

**Request Body:**
```json
{
  "name": "February 2025 Schedule",
  "description": "Monthly schedule for training period",
  "event_id": 1,
  "soldiers_ids": [7, 8, 9]
}
```

**Response:**
```json
{
  "id": 3,
  "name": "February 2025 Schedule",
  "description": "Monthly schedule for training period",
  "event": {
    "id": 1,
    "name": "Training Exercise",
    "event_type": "TRAINING",
    "description": "Advanced military training",
    "start_date": "2025-02-01",
    "end_date": "2025-02-28",
    "min_required_soldiers_per_day": 8,
    "base_days_per_soldier": 14,
    "home_days_per_soldier": 13,
    "max_consecutive_base_days": 5,
    "max_consecutive_home_days": 8,
    "min_base_block_days": 2,
    "created_by": null,
    "created_at": "2025-08-10T03:24:14.719808Z"
  },
  "soldiers": [
    {
      "id": 7,
      "name": "John Doe",
      "soldier_id": "S001",
      "rank": "SERGEANT",
      "constraints_count": 3,
      "is_exceptional_output": true,
      "is_weekend_only_soldier_flag": false
    },
    {
      "id": 8,
      "name": "Soldier 1",
      "soldier_id": "BULK001",
      "rank": "PRIVATE",
      "constraints_count": 0,
      "is_exceptional_output": false,
      "is_weekend_only_soldier_flag": false
    },
    {
      "id": 9,
      "name": "Soldier 2",
      "soldier_id": "BULK002",
      "rank": "CORPORAL",
      "constraints_count": 1,
      "is_exceptional_output": true,
      "is_weekend_only_soldier_flag": false
    }
  ],
  "soldiers_count": 3,
  "status": "PENDING",
  "solution_details": null,
  "processing_time_seconds": null,
  "created_by": null,
  "created_by_username": null,
  "created_at": "2025-08-10T03:24:50.071652Z"
}
```

### Execute Algorithm
**Endpoint:** `POST /api/scheduling-runs/{id}/execute_algorithm/`

**Request Body:** Empty

**Successful Response:**
```json
{
  "message": "Algorithm executed successfully",
  "assignments_created": 84
}
```

**Error Response:**
```json
{
  "error": "No feasible solution found"
}
```

**Status Values:** `PENDING`, `IN_PROGRESS`, `SUCCESS`, `FAILURE`, `NO_SOLUTION`, `CANCELLED`

### List Scheduling Runs
**Endpoint:** `GET /api/scheduling-runs/`

**Query Parameters:**
- `event`: Filter by event ID
- `status`: Filter by status

---

## 5. Assignments API (Read-Only)

### List Assignments
**Endpoint:** `GET /api/assignments/`

**Query Parameters:**
- `scheduling_run`: Filter by scheduling run ID
- `soldier`: Filter by soldier ID
- `start_date`: Filter from this date
- `end_date`: Filter until this date
- `is_on_base`: Filter by assignment type (`true`/`false`)

**Response:**
```json
{
  "count": 84,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "scheduling_run": 3,
      "scheduling_run_name": "February 2025 Schedule",
      "soldier": {
        "id": 7,
        "name": "John Doe",
        "soldier_id": "S001",
        "rank": "SERGEANT",
        "constraints_count": 3,
        "is_exceptional_output": true,
        "is_weekend_only_soldier_flag": false
      },
      "assignment_date": "2025-02-01",
      "is_on_base": true
    }
  ]
}
```

### Calendar View
**Endpoint:** `GET /api/assignments/calendar/`

**Query Parameters:**
- `scheduling_run`: Required - scheduling run ID

**Response:**
```json
{
  "2025-02-01": {
    "on_base": [
      {
        "id": 7,
        "name": "John Doe",
        "rank": "SERGEANT"
      },
      {
        "id": 8,
        "name": "Soldier 1",
        "rank": "PRIVATE"
      }
    ],
    "at_home": [
      {
        "id": 9,
        "name": "Soldier 2",
        "rank": "CORPORAL"
      }
    ]
  },
  "2025-02-02": {
    "on_base": [
      {
        "id": 9,
        "name": "Soldier 2",
        "rank": "CORPORAL"
      }
    ],
    "at_home": [
      {
        "id": 7,
        "name": "John Doe",
        "rank": "SERGEANT"
      },
      {
        "id": 8,
        "name": "Soldier 1",
        "rank": "PRIVATE"
      }
    ]
  }
}
```

---

## Complete Workflow Example

### Step 1: Create an Event
```bash
curl -X POST "http://localhost:8000/api/events/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Monthly Training",
    "event_type": "TRAINING",
    "start_date": "2025-03-01",
    "end_date": "2025-03-31",
    "min_required_soldiers_per_day": 5,
    "base_days_per_soldier": 15,
    "home_days_per_soldier": 16
  }'
```

### Step 2: Create Soldiers with Constraints
```bash
curl -X POST "http://localhost:8000/api/soldiers/bulk_create/" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "name": "Alice Smith",
      "soldier_id": "A001",
      "rank": "CAPTAIN",
      "is_exceptional_output": true,
      "constraints_data": [
        {
          "constraint_date": "2025-03-15",
          "constraint_type": "PERSONAL",
          "description": "Wedding"
        }
      ]
    },
    {
      "name": "Bob Johnson",
      "soldier_id": "B002",
      "rank": "SERGEANT",
      "is_exceptional_output": false
    },
    {
      "name": "Carol Wilson",
      "soldier_id": "C003",
      "rank": "PRIVATE",
      "is_weekend_only_soldier_flag": true
    }
  ]'
```

### Step 3: Create Scheduling Run
```bash
curl -X POST "http://localhost:8000/api/scheduling-runs/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "March 2025 Schedule",
    "description": "Monthly training schedule",
    "event_id": 1,
    "soldiers_ids": [1, 2, 3]
  }'
```

### Step 4: Execute Algorithm
```bash
curl -X POST "http://localhost:8000/api/scheduling-runs/1/execute_algorithm/" \
  -H "Content-Type: application/json"
```

### Step 5: View Results
```bash
# Get assignments in calendar format
curl "http://localhost:8000/api/assignments/calendar/?scheduling_run=1"

# Get all assignments for a specific soldier
curl "http://localhost:8000/api/assignments/?soldier=1&scheduling_run=1"
```

---

## Error Handling

All endpoints return proper HTTP status codes and JSON error responses:

### Validation Errors (400 Bad Request)
```json
{
  "field_name": ["Error message describing the validation issue"]
}
```

### Not Found Errors (404 Not Found)
```json
{
  "detail": "Not found."
}
```

### Server Errors (500 Internal Server Error)
```json
{
  "error": "Description of the server error"
}
```

---

## Tips for Frontend Integration

1. **Content-Type**: Always set `Content-Type: application/json` for POST/PUT requests
2. **Date Format**: Use ISO format `YYYY-MM-DD` for dates
3. **Boolean Values**: Use `true`/`false` (lowercase) for boolean fields
4. **Validation**: Check response status codes and handle validation errors appropriately
5. **Nested Creation**: Use `constraints_data` field to create soldier constraints in the same request
6. **Bulk Operations**: Use bulk endpoints for better performance when creating multiple records
7. **Filtering**: Use query parameters for filtering and searching
8. **Real-time Updates**: Poll the scheduling run status during algorithm execution

This API provides a complete JSON interface for managing military scheduling with comprehensive validation, error handling, and flexible data management capabilities.