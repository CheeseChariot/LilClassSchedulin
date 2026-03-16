# API Reference

The app exposes lightweight JSON routes.

## `GET /api/teachers`

Returns all teacher profiles.

Response: `200 OK`

```json
[
  {
    "id": "example_teacher",
    "name": "Example Teacher",
    "classes": []
  }
]
```

## `GET /api/students`

Returns all student profiles.

Response: `200 OK`

## `GET /api/student/<student_id>/kardex`

Returns normalized kardex for the student.

Responses:
- `200 OK` with kardex JSON
- `404 Not Found` if student does not exist

## `GET /api/classrooms`

Returns all classroom profiles.

Response: `200 OK`

## `GET /api/badges`

Returns badges JSON.

Response: `200 OK`

## `GET /api/progression`

Returns progression requirements JSON.

Response: `200 OK`

## Notes

- API routes are read-only in the current implementation.
- UI forms perform writes through non-API POST routes.
