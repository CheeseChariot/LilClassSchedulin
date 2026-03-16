# Data Model

All data is stored as JSON files under `data/`.

## Teacher (`data/teacher/<teacher_id>.json`)

```json
{
  "id": "example_teacher",
  "name": "Example Teacher",
  "classes": [
    {
      "id": "math101",
      "name": "Math 101",
      "schedule": {
        "monday": "09:00-11:00"
      },
      "status": "active"
    }
  ]
}
```

## Student (`data/student/<student_id>.json`)

```json
{
  "id": "example_student",
  "name": "Example Student",
  "career": [
    {
      "class_id": "math101",
      "class_name": "Math 101",
      "status": "Untaken"
    }
  ]
}
```

Allowed student statuses:
- `Untaken`
- `Pass`
- `Fail`
- `Retry`
- `Force`
- `Taken`

Status semantics:
- `Untaken`: course not chosen or not taken yet
- `Taken`: course currently being taken
- `Pass`: course completed successfully
- `Fail`: course failed and not retaken yet
- `Retry`: required retake after failing a required course
- `Force`: course taken early or over a prerequisite

## Kardex (`data/kardex/<student_id>.json`)

```json
{
  "student_id": "example_student",
  "student_name": "Example Student",
  "entries": [
    {
      "class_id": "math101",
      "class_name": "Math 101",
      "status": "Pass",
      "grade": 8.5,
      "period": "2024-1",
      "notes": "Good progress"
    }
  ]
}
```

Kardex status is synchronized from student career status.

## Classroom (`data/classroom/<classroom_id>.json`)

```json
{
  "id": "room_101",
  "name": "Room 101",
  "location_guide": "Building A, ground floor",
  "capabilities": "Projector, whiteboard, Wi-Fi",
  "space_sqm": 50,
  "chairs": 30,
  "description": "General purpose lecture room"
}
```

## Course Catalog (`data/courses.json`)

```json
{
  "program_name": "Ingenieria Civil en Computacion e Informatica",
  "plan_year": 2020,
  "source": "General course metadata catalog",
  "courses": [
    {
      "course_id": "matematica_i",
      "course_name": "Matematica I",
      "semester": 1,
      "hp": 174.0,
      "hnp": 232.0,
      "ct": 14,
      "duration": "S"
    }
  ]
}
```

Course catalog entries use a global semester index (`1..12`).
Legacy data containing `year` plus local `semester` is normalized into a single semester number on load.

## Semester Schedule (`data/schedules/<semester>.json`)

```json
{
  "semester": "2026_1",
  "default_group": "group_1",
  "university": "Universidad de Magallanes",
  "program": "Ingenieria Civil en Computacion e Informatica",
  "plans": ["informatica", "civil"],
  "classes": [
    {
      "class_id": "ingenieria_software_civ_s9",
      "class_name": "Ingenieria de Software",
      "plan": "civil",
      "academic_semester": 9,
      "teacher_ids": ["kg"],
      "status": null,
      "times": [
        {
          "day": "tuesday",
          "block": "b2",
          "group": null,
          "room": "redes",
          "tipo": null
        }
      ]
    }
  ]
}
```

Schedule normalization preserves optional root metadata (`university`, `program`, `plans`), per-class `plan` and `academic_semester`, and per-slot `room` and `tipo` fields.

## Badges (`data/badges.json`)

```json
{
  "badges": [
    {
      "id": "first_pass",
      "name": "First Pass",
      "description": "Pass your first class",
      "achieved": false
    }
  ]
}
```

## Progression (`data/progression.json`)

```json
{
  "requirements": [
    {
      "badge_id": "first_pass",
      "description": "Pass at least 1 class"
    }
  ]
}
```

## Normalization Behavior

When JSON files are loaded, the app normalizes:
- missing lists to empty lists
- invalid numeric fields to `null`
- invalid status values to `Untaken` (student/kardex contexts)
- malformed IDs to slug-safe IDs when possible
