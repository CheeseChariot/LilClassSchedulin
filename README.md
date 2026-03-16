# LilClassSchedulin

LilClassSchedulin is a local Flask web app for tracking:
- teachers and their classes
- students and career status by class
- kardex records (grade, period, notes)
- classrooms, badges, and progression requirements

This project stores data as JSON files in `data/`, so it can run without a database server.

## Requirements

- Windows PowerShell (this README is PowerShell-first)
- Python 3.10+ (recommended 3.11 or 3.12)
- Git (optional but recommended)

Only one Python package is required by the project:
- `flask>=3.0.0`

## First-Time Setup (PowerShell)

### 1. Check what is installed

```powershell
Get-Command python, py, pip, git -ErrorAction SilentlyContinue |
	Select-Object Name, Source
```

If `python --version` prints a Microsoft Store message like "Python was not found", Python is not installed yet (you only have the Windows alias).

### 2. Install Python

Option A (recommended): install from https://www.python.org/downloads/ and enable "Add python.exe to PATH" during install.

Option B (winget):

```powershell
winget install --id Python.Python.3.12 -e
```

Then open a new PowerShell window and verify:

```powershell
python --version
```

### 3. Clone and enter the repo

```powershell
git clone https://github.com/CheeseChariot/LilClassSchedulin.git
Set-Location .\LilClassSchedulin
```

### 4. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If activation is blocked by PowerShell policy:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 5. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 6. Run the app

```powershell
python app.py
```

Open `http://127.0.0.1:5000`.

## What Happens on Startup

The app now performs an initial bootstrap:
- ensures `data/` subfolders exist
- ensures `data/badges.json` and `data/progression.json` exist with valid top-level structure
- tolerates missing/legacy fields in teacher/student/classroom/kardex JSON files via normalization

This makes first run and old data files more resilient.

## Main Routes

- `/` dashboard
- `/teachers`, `/teacher/<teacher_id>`
- `/students`, `/student/<student_id>`
- `/student/<student_id>/kardex`
- `/classrooms`, `/classroom/<classroom_id>`
- `/badges`, `/progression`

JSON API routes:
- `/api/teachers`
- `/api/students`
- `/api/student/<student_id>/kardex`
- `/api/classrooms`
- `/api/badges`
- `/api/progression`

## Documentation

Detailed docs are in `doc/`:
- `doc/01-system-overview.md`
- `doc/02-setup-windows-powershell.md`
- `doc/03-data-model.md`
- `doc/04-workflows.md`
- `doc/05-api-reference.md`
- `doc/06-troubleshooting.md`

## Development Notes

- Data is file-based JSON (no SQL migrations needed).
- IDs are slug-like and derived from names for routing/file names.
- Student career status is treated as source of truth and synced into kardex status.
