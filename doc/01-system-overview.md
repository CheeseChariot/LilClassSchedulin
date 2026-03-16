# System Overview

## Purpose

LilClassSchedulin is a local department management app built with Flask.
It tracks:
- teachers and classes
- students and class status progression
- kardex details per class (grade, period, notes)
- classrooms and basic capabilities
- badges and progression requirements

## Architecture

- Backend: Flask app in `app.py`
- Frontend: Jinja templates in `templates/` and CSS in `static/css/style.css`
- Persistence: JSON files under `data/`

There is no database server. Data is loaded and saved directly from files.

## Directory Layout

- `app.py`: all routes and helper logic
- `templates/`: HTML views
- `static/css/style.css`: styles
- `data/teacher/`: teacher profiles
- `data/student/`: student profiles
- `data/kardex/`: kardex by student id
- `data/classroom/`: classroom profiles
- `data/badges.json`: badges list
- `data/progression.json`: progression requirements

## Startup Behavior

On startup, the app ensures:
- required `data/` folders exist
- `badges.json` has a valid root structure
- `progression.json` has a valid root structure

During requests, loaded JSON data is normalized in memory, so older or partial files do not crash route handlers.

## Data Flow Summary

1. User action from HTML form submits to a POST route.
2. Route loads and normalizes target JSON file.
3. Route validates input and updates model.
4. JSON is saved back to disk.
5. Route redirects to a GET page.

## Source of Truth Note

Student `career` statuses are the source of truth.
Kardex status fields are synchronized from student career entries.
