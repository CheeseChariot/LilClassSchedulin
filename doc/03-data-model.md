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
